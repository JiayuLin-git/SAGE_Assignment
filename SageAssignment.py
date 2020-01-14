import urllib3
import requests
import csv
import codecs
import json
import re
import time
import sys
import pandas as pd
import datetime
from bs4 import BeautifulSoup

def string_cleaning(result):
    a = result.text
    a = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", a)
    a = a.strip()
    return a

def result_Check(list):
    if 'Successful' in list or 'Operational'in list or 'En Route' in list:
        return 1
    else:
        return 0

def date2ISO8601(df_result,Year=2019):
    res_list=[]
    for res in df_result['date']:
        b = datetime.datetime.strptime(res, '%d %B')
        b = b.replace(year=Year)
        rt_format=str(b.isoformat())+"+00:00"
        res_list.append(rt_format)
    df_result['date']=res_list
    return 0

def dateRange(beginDate, endDate):
    dates = []
    dt = datetime.datetime.strptime(beginDate, "%Y-%m-%d")
    dt_end = datetime.datetime.strptime(endDate, "%Y-%m-%d")
    while dt <= dt_end:
        rt_format=str(dt.isoformat())+"+00:00"
        dates.append(rt_format)
        dt = dt + datetime.timedelta(1)
    return dates

if __name__=="__main__":
    #request crawel the data
    list = []
    r = requests.get("https://en.wikipedia.org/wiki/2019_in_spaceflight#Orbital_launches")
    soup = BeautifulSoup(r.content, 'html.parser')
    tables = soup.find_all("table", attrs={"class": "wikitable collapsible"})
    right_table = tables[0]
    trs = right_table.find_all('tr')

    current_time = ''
    current_result = []
    temp_time = ''
    temp_result = []

    #get the original data
    for tr in trs:
        # get time
        time = tr.find('span', {'class': 'nowrap'})

        if time != None:
            temp_time = time.text
            temp_time=temp_time.replace(u'\xa0?',u' ')
            a = re.sub(u"\\(.*?\\)|\\{.*?}|\\[.*?]", "", temp_time)
            temp_time = a.strip()
            temp_result = []
        else:
            temp_time = ''
            temp_result = []
        results = tr.find_all('td', {'rowspan': '1'})
        for result in results:
            temp=result.find('span', {'class': 'nowrap'})
            if(temp):
                temp_result.append(temp.text)
                continue
            a = string_cleaning(result)
            temp_result.append(a)

        # The date is the Decay data
        if (temp_time):
            # failed date etc..
            if temp_time in temp_result:
                for result in results:
                    a = string_cleaning(result)
                    current_result.append(a)
            else:
                if current_result != []:
                    list.append([current_time, current_result])
                current_time = temp_time
                current_result = temp_result
        else:
            # no date specified
            for result in results:
                a=string_cleaning(result)
                current_result.append(a)

    #transform to dataframe
    df_result = pd.DataFrame(columns=['date', 'value'],index=None, data=list)

    #replace result with count
    count_list=[]
    for res in df_result['value']:
        count_list.append(result_Check(res))
    df_result['value']=count_list

    #transform date to ISO8601
    date2ISO8601(df_result)

    #create all days in 2019 with ISO8601FORMAT
    all_date_list=dateRange('2019-01-01', '2019-12-31')
    df_all=pd.DataFrame(columns=['date'],index=None,data=all_date_list)
    df_all['value']=0

    #merge two DataFrame
    df_all=pd.concat([df_all,df_result],sort=False)
    df_all=df_all.groupby('date').sum()

    #savetocsv
    df_all.to_csv('ans.csv',encoding='utf-8')