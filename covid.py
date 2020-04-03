import csv
import datetime
import math
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas
import sys
import xlrd

from scipy.optimize import curve_fit

#predicted cases, based on time
def func_logistic(date_delta, max_infection, steepness, crossover):
    val = max_infection/(1+np.exp(-steepness*(date_delta-crossover)))
    #print(val)
    return val
#enddef

def func_logistic_deriv(date_delta, max_infection, steepness, crossover):
    val = np.exp(-(date_delta - crossover)*steepness)/((1/steepness)*(1+np.exp(-(date_delta - crossover)*steepness))**2)*max_infection
    return val
#enddef

def format_data(ldates, ddates, lcases):
    mdates = []
    mdiff  = []
    mcases = []
    for i in range(0,len(ldates)):
        
        if lcases[i] > 0:
            mdates.append(ldates[i])
            mdiff.append(ddates[i])
            mcases.append(lcases[i])
            #a_data.append([ldates[i], ddates[i], lcases[i]])
            #print(ldates[i], ddates[i], lcases[i])
    #endfor
    #print(mdates,mdiff,mcases)
    return(mdates, mdiff, mcases)
#enddef

def get_year(base, date_first):
    x2data_full = np.arange(base,np.datetime64('2021-01-01'))
    xdata_full = []
    for i in x2data_full:
        if i < np.datetime64(date_first):
            xdata_full.append(0)
        else:
            diff = (i - np.datetime64(date_first))/np.timedelta64(1,'D')
            xdata_full.append(diff)
        #endif
    #endfor
    xdata_full = np.array(xdata_full)

    return x2data_full, xdata_full
#enddef

def run_cases_model(confirmed_cases_df, population, geo_area, showplot):
    
    infection_rate = 1.0 #100% of people get infected
    max_infection  = population * infection_rate
    steepness      = 0.26437837  #initial guess - copy from org model to make sure code is working
    crossover      = 46.7794536  #initial guess
    
    #column where data starts
    data_col = 11
    cases_df = confirmed_cases_df.iloc[:,data_col:]
    cases_df = cases_df.T
    tlcases = cases_df.values.tolist()
    lcases = []
    #find out when first non zero cases was
    i = 0
    non_zero = False
    for c in tlcases:
        [x] = c
        lcases.append(x)
        if x < 1:
            i = i + 1
        else:
            non_zero = True
        #endif
    #endfor
        
    if non_zero == False:
        peak_date  = "Unk"
        peak_cases = "Unk"
    else:
        dates_df = confirmed_cases_df.columns[data_col:].to_series().reset_index(drop=True)
        #dates_df = pandas.to_datetime(dates_df)
        tldates = dates_df.values.tolist()
        ldates = []
        ddates = []
        j = 0
        for d in tldates:
            try:
                do = datetime.datetime.strptime(d,"%m/%d/%Y")
            except:
                do = datetime.datetime.strptime(d,"%m/%d/%y") #somebody screwed up the upload, read 2-digit dates
            ldates.append(do)
            if j <= i:
                ddates.append(0)        
            else:
                ddates.append(j-i)
            #endif
            j = j + 1
                
        #endfor
        
        date_first = ldates[i]
        #print(date_first)
        """
        print(infection_rate)
        print(max_infection)
        print(steepness)
        print(crossover)
        print(date_first)
        print(lcases[i])
        #print(cases_df)
        #print(dates_df)
        print(ddates)
        #print(lcases, ldates)
        """   
        (mdates, mdiff, mcases) = format_data(ldates, ddates, lcases)
        
        #plt.plot(dates_df,cases_df)
        #plt.show()
            
        #date_peak      = date_first + crossover  #date_first is first day cases reported

        # predict cases
        """
        a_cases_diff = []
        for i in range(1,10):
            cases_pred = int(round(func_logistic(i, max_infection, steepness, crossover),0))
            print(cases_pred)
            #a_cases_diff.append(cases_actual - cases_pred)
        # endfor
        #print(a_cases_diff)
        return
        """

        xdata  = np.array(mdiff)
        x2data = np.array(mdates)
        ydata  = np.array(mcases)
        
        base = np.datetime64('2020-01-01')
        x2data_full, xdata_full = get_year(base, date_first)
        
        #picked these because they seem reasonable
        stp_lower = 0.1
        stp_upper = 0.7
        co_lower  = 0.0
        co_upper  = 180.0
        
        
        popt, pcov = curve_fit(func_logistic, xdata, ydata, bounds=((max_infection-0.01,stp_lower,co_lower),(max_infection,stp_upper,co_upper)))
        #print(popt)
        #plt.plot(xdata,ydata)
        if showplot == True:
            plt.title(geo_area + "\n" + "Current Cases: " + str(mcases[-1]))
            plt.plot(x2data_full, func_logistic(xdata_full, *popt))
            plt.plot(x2data, ydata, 'r-')
            plt.show()
        #endif
        
        peak_cases =  str(int(round(np.max(func_logistic_deriv(xdata_full,*popt)))))
        index      = np.where(func_logistic_deriv(xdata_full,*popt) == np.amax(func_logistic_deriv(xdata_full,*popt)))
        iday       = index[0][0]
        peak_date  = str(x2data_full[iday])
        
        if showplot == True:
            plt.title(geo_area + "\n" + "Peak Date: " + peak_date + "\n" + "Peak Cases: " + peak_cases)
            plt.plot(x2data_full, func_logistic_deriv(xdata_full, *popt))
            plt.show()
        #endif
    #endif
    
    return (peak_date, peak_cases)
#enddef

#read the covid data (maybe here check if new or not then get from github)
#covid deaths has population as a column (confirmed does not)
def get_covid(data, geo_area):
    #if old get the covid data from github
    dfile = os.path.join(os.getcwd(),"time_series_covid19_"+data+"_US.csv")
    df = pandas.read_csv(dfile)
    
    if "," in geo_area:
        a_geo_area = geo_area.split(',')
        county = a_geo_area[0].strip()
        county = county.replace('County','')
        county = county.strip()
        state  = a_geo_area[1].strip()
    else:
        county = ""
        state = geo_area
    #endif
        
    mask = (df['Admin2']== county) & (df['Province_State']== state)
    result = df[mask]
    #print(result)
    #a = df.columns.to_series().reset_index(drop=True)
    #print(a)
    
    return result
#enddef

def main():
    #get the geographic area and population estimate for 2019
    cfile = os.path.join(os.getcwd(),"co-est2019-annres.xlsx") #USA (reads this in order that's why results are in order)
    #cfile = os.path.join(os.getcwd(),"co-est2019-annres-45.xlsx")  #SC
    wb    = xlrd.open_workbook(cfile)
    sheet = wb.sheet_by_index(0)
    sheet.cell_value(0,0)
    #for all the counties in South Carolina (see co-est2019-annres-45.xlsx)
    for i in range(sheet.nrows):
        first_col = sheet.cell_value(i,0)
        if "Note:" in first_col:
            break
        #endif
        #get the population for the area
        if i < 5:  #row 5 is Abbeville County (first county by alphabetical) in SC data (this may mess up if doing whole USA)
            pass
        else:
            if first_col[0] == ".":
                geo_area = first_col[1:]          #trim off leading "."
            else:
                geo_area = first_col
            geo_area = geo_area.strip()
            pop      = sheet.cell_value(i,12) #this is should be an int, but probably treated as a float
                        
            states = ["Washington"]
            ny   = ["King"] #,"Richmond","Westchester","Bergen","Huson","Passaic", "Putnam","Rockland"]
            
            #states = ["California"]
            #ny     = ["Orange"]
            
            results = []
            peak_dates = []
            peak_cases = []
            
            showplot   = True
            #showplot   = False
            peak_date  = ""
            peak_cases = ""
            
            for s in states:
                if s in geo_area:
                    for c in ny:
                        if c in geo_area:        
                            #get the number of covid cases (from time_series..._confirmed_US)        
                            confirmed_cases_df = get_covid("confirmed", geo_area)
                            
                            peak_date, peak_cases = run_cases_model(confirmed_cases_df, pop, geo_area, showplot)
                            
                            #results.append([s, c, peak_date, peak_cases])
                            print(s, c, pop, peak_date, peak_cases)
                        #endif
                    #endfor
                #endif
            #endfor
            
            states = ["South Carolina","Georgia"]
            csra = ["Aiken", "Edgefield","Barnwell","Saluda","Bamberg","McCormick","Allendale","Richmond", "Columbia", "Burke","McDuffie", "Washington", "Jefferson", "Screven", "Wilkes", "Jenkins", "Hancock", "Lincoln", "Warren", "Glascock", "Taliaferro"]
            
            results = []
            peak_dates = []
            peak_cases = []
            
            showplot   = True
            #showplot   = False
            peak_date  = ""
            peak_cases = ""
            
            for s in states:
                if s in geo_area:
                    for c in csra:
                        if c in geo_area:        
                            #get the number of covid cases (from time_series..._confirmed_US)        
                            confirmed_cases_df = get_covid("confirmed", geo_area)
                            
                            peak_date, peak_cases = run_cases_model(confirmed_cases_df, pop, geo_area, showplot)
                            
                            #results.append([s, c, peak_date, peak_cases])
                            print(s, c, pop, peak_date, peak_cases)
                        #endif
                    #endfor
                #endif
            #endfor
            
            
            states = ["Washington"]
            hanford = ["Benton","Franklin","Walla Walla"]
            
            for s in states:
                if s in geo_area:
                    for c in hanford:
                        if c in geo_area:        
                            #get the number of covid cases (from time_series..._confirmed_US)        
                            confirmed_cases_df = get_covid("confirmed", geo_area)
                            
                            peak_date, peak_cases = run_cases_model(confirmed_cases_df, pop, geo_area, showplot)
                            
                            #results.append([s, c, peak_date, peak_cases])
                            print(s, c, pop, peak_date, peak_cases)
                        #endif
                    #endfor
                #endif
            #endfor
            
            states   = ["Tennessee"]
            oakridge = ["Anderson","Roane"]
            
            for s in states:
                if s in geo_area:
                    for c in oakridge:
                        if c in geo_area:        
                            #get the number of covid cases (from time_series..._confirmed_US)        
                            confirmed_cases_df = get_covid("confirmed", geo_area)
                            
                            peak_date, peak_cases = run_cases_model(confirmed_cases_df, pop, geo_area, showplot)
                            
                            #results.append([s, c, peak_date, peak_cases])
                            print(s, c, pop, peak_date, peak_cases)
                        #endif
                    #endfor
                #endif
            #endfor
                        
            
            #break
            
            #get the number of covid deaths (from time_series..._deaths_US)
            #confirmed_mort_df  = get_covid("deaths", geo_area)
            
        #endif
    #endfor
#enddef

if __name__ == "__main__":
    main()
    sys.exit()


