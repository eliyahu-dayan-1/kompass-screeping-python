#!/usr/bin/env python
# coding: utf-8

# In[11]:


import os
import json
import csv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import os
from bs4 import BeautifulSoup
import time
import copy
from pathlib import Path
import time
import uuid
import re


# In[24]:


def config_relative_path(path):
    os.chdir( path )
    return "the relative path is %s" %os.getcwd()


#the function get url load hime and return the pagesource
def openUrl(url):
    browser.get(url)
    time.sleep(2)
    return browser.page_source

def remove_bad_file_char(string):
    return re.sub('[^\w\-_\. ]', '_', string)

#get links of all cantry
#url is https://us.kompass.com/selectcountry/ download with powershell
def get_country_links():

    country_links_html = BeautifulSoup(open("%s/download-htmls/country-links" %path))
    country_links = country_links_html.findAll("div", {"class": "container countries-liste"})[0].findAll("a")
    country_links = [[link.get('href'), link.text] for link in country_links]

    with open("kompass_country_links.txt", "w") as txt_file:
        for line in country_links:
            txt_file.write(line[0] + "\n") # works with any number of elements in a line
    
    return country_links


def openDirectory(path):
    if not os.path.exists("./" + path):
        os.makedirs("./" + path)
        print('new directory maked')

    else:
        print('directory alredy exist')

def get_all_category_links(html):

    soup = BeautifulSoup( html, 'html.parser')
    mydivs = soup.findAll("ul", {"class": "seoAllActivitiesUl"})[0].findAll("a")

    category_links = []
    for index, a in enumerate(mydivs):
        new_link = {}
        new_link['link'] = a.get('href')
        new_link['category'] = a.text
        category_links.append(copy.deepcopy(new_link))
        print("get link %s from %s" %(index, len(mydivs)))
    
    return category_links

def get_sub_links(html, category_link):
    soup = BeautifulSoup(html, 'html.parser')
    category_link['num_of_company'] = soup.findAll("span", {"class": "btn-filter filterEnterprise"})[0].findAll("span")[0].text
    category_link['num_of_company'] = int(category_link['num_of_company'].replace(",", ""))
    category_link['sub_links'] = recurtion_sub_link(soup, category_link['num_of_company'])
    return category_link

def recurtion_sub_link(soup, num_of_company):
    global sum_all_company
    sum_company = 0
#     sub_links = [a.get('href') for a in soup.findAll("div", {"class": "search_facet"})[1].findAll("a")]
    sub_links_divs = soup.select(".search_facet .facetValues")
    sub_links = [a.get('href') for a in sub_links_divs[1].findAll("a")]
    if(len(sub_links) == 0): sub_links = [a.get('href') for a in sub_links_divs[0].findAll("a")]
    if(num_of_company > 1700):
        sub_sub_links = []
        for sub_link in sub_links:
            print("treat sub link " + sub_link)
            sub_link_html = loadCompnyListHtml(sub_link)   
            soup = BeautifulSoup(sub_link_html, 'html.parser')
            num_of_company = soup.findAll("span", {"class": "btn-filter filterEnterprise"})
            num_of_company  = num_of_company[0].findAll("span")[0].text
            num_of_company = int(num_of_company.replace(",", ""))
            if(num_of_company < 1700):
                sum_company += num_of_company
                sum_all_company += num_of_company
                print("good link")
                sub_sub_links.append(sub_link)
            else:
                print("recurtion in")
                sub_sub_links.append(recurtion_sub_link(soup, num_of_company))
        print('sum of company is %s' % sum_company)
        return flatten(sub_sub_links) 
    else:
        sum_company = num_of_company
        sum_all_company += num_of_company
        print("return sub link")
        print('sum of company is %s' % sum_company)
        return sub_links
    
def flatten(S):
    if S == []:
        return S
    if isinstance(S[0], list):
        return flatten(S[0]) + flatten(S[1:])
    return S[:1] + flatten(S[1:])

def saveHtml(html_source, country_link, relative_path):
    with open(relative_path , "w", encoding="utf-8") as f:
        f.write(html_source)
        print("save %s" %(relative_path))

def loadCompnyListHtml(path):
    df1 = df_loaded_html[df_loaded_html['url'].str.contains(path)]
    if len(df1.index):
        print('exist yet, load from directory')
        print(df1.iloc[0].loc['relative_directory'])
        relative_directory = df1.iloc[0].loc['relative_directory']
        return open(relative_directory, encoding="utf8")
    else:
        company_list_html = openUrl(path)
        soup = BeautifulSoup("%s" % company_list_html, 'html.parser')
        curr_country_link = soup.findAll("a", {"id": "headerKompassLogo"})[0].get('href')[8:]
        openDirectory(curr_country_link)

        curr_category = soup.find("div", {"id": "introContentTitle"}).find("h1").text
        curr_category = remove_bad_file_char(" ".join(curr_category.split()))
        
        num_of_company = soup.findAll("span", {"class": "btn-filter filterEnterprise"})
        num_of_company  = num_of_company[0].findAll("span")[0].text
        num_of_company = int(num_of_company.replace(",", ""))
        
        paginationDiv = soup.findAll("ul", {"class": "pagination"})
        curr_pagination = paginationDiv[0].select(".searchItemLi.active")[0].text if len(paginationDiv) else 1
        if curr_pagination != 1: 
            curr_pagination = "".join(curr_pagination.split())
        number_of_itreation = 1;
        if len(paginationDiv) > 0:
            paginationDiv = paginationDiv[0].findAll("a")
            if "svg" in str(paginationDiv[-1]):
                number_of_itreation = int(paginationDiv[-2].text)
            else:
                number_of_itreation = int(paginationDiv[-1].text)
        relative_path = "./%s/%s-%s-%s.html" %(countryPath, curr_category, curr_pagination, uuid.uuid1())
        saveHtml(company_list_html, countryPath, relative_path)
        write_saved_html_to_df(path, curr_category, relative_path, num_of_company, curr_pagination, number_of_itreation)
        return company_list_html
                
    
def write_saved_html_to_df(path ,curr_category ,relative_path, num_of_company, curr_pagination, number_of_itreation):
    global df_loaded_html

    data_saved_html = {}
    data_saved_html['url'] = path
    data_saved_html['saved_time'] = time.time()
    data_saved_html['relative_directory'] = relative_path
    data_saved_html['absolute_dir'] = "C:/Users/USER/Desktop/pythonLearning/kompassScriping/" + relative_path
    data_saved_html['number_of_itreation'] = number_of_itreation
    data_saved_html['curr_page'] = curr_pagination
    data_saved_html['num_of_company'] = num_of_company

    df_loaded_html= df_loaded_html.append(data_saved_html, ignore_index=True)
    print("write %s in df" % relative_path)
    
def get_all_paginaiton(index, row):

        if row['curr_page'] == 1 and row['num_of_company'] < 1700 :
            company_list_html = loadCompnyListHtml(row['url'])
            soup = BeautifulSoup(company_list_html, 'html.parser')
            curr_country_link = soup.findAll("a", {"id": "headerKompassLogo"})[0].get('href')[8:]
            curr_category = soup.find("div", {"id": "introContentTitle"}).find("h1").text
            curr_category = remove_bad_file_char(" ".join(curr_category.split()))
            paginationDiv = soup.findAll("ul", {"class": "pagination"})
            number_of_itreation = row['number_of_itreation']
            for page in range(number_of_itreation):
                page += 1
                print(page)
                if page == 1:
                    continue
                loadCompnyListHtml(row['url'] + "/page-%s" % page)
            df_loaded_html.to_csv('./%s/loaded_html.csv' % countryPath)

def parse_company_list_html(index, row, csv_path):
    
    global df_compnies_details

    print(row['relative_directory'])
    companies_html = BeautifulSoup(open(row["relative_directory"], encoding="utf8"))
    try:
        country_links_html = companies_html.find("div", {'id', "resultatDivId"})
        if(country_links_html == None): return
        country_links_html = country_links_html.findAll('div', {'class', 'prod_list'})
    except:
        print('cant load' + filename)
        return
    for counter, company_div in enumerate(country_links_html):
        data = {}

        try:
            data['kompass_id'] = company_div.select('.row .rowFooter .list-buttons-container input')[-1].get('value')
            print(data['kompass_id'])
            df1 = df_compnies_details[df_compnies_details['kompass_id'].str.contains(data['kompass_id'])]
            if len(df1.index):
                print('the company %s has allredy exist' % data['kompass_id'])
                continue
        except:
             print("is note exist")
        try:
            data['phone'] = company_div.select('a.coordonneesItemLink.showMobile')[-1].text
            data['phone'] = ' '.join(data['phone'].split())
        except:
            print("dont get phone")
        try:
            data['country'] = company_div.select('.flagWorld .placeText')[0].text
        except:
            print("dont get country")
        try:
            data['description'] = company_div.select('.product-summary a')[0].text
        except:
            print("dont get description")
        try:
            data['company_name'] = company_div.select('.product-list-data h2 a')[0].text
            data['company_name'] = ' '.join(data['company_name'].split())
        except:
            print("dont get company name")
        try:
            data['url'] = company_div.select('.product-list-data h2 a')[0].get('href')
        except:
            print("dont get url")
        try:
            data['company_list_url'] = row['url']
        except:
            print("dont get company list url")
        try:
            data['company_list_file_directory'] = row['relative_directory']
        except:
            print("dont get company list file name")
        df_compnies_details = df_compnies_details.append(data, ignore_index=True)
        print("append" + str(counter))

#     if index % 100 == 0: 
    df_compnies_details.to_csv(csv_path)


# In[25]:


torexe = os.popen(r'C:/Users/USER/Desktop/Tor Browser/Browser/TorBrowser/Tor/tor.exe')
profile = FirefoxProfile(r'C:\Users\USER\Desktop\Tor Browser\Browser\TorBrowser\Data\Browser\profile.default')
profile.set_preference('network.proxy.type', 1)
profile.set_preference('network.proxy.socks', '127.0.0.1')
profile.set_preference('network.proxy.socks_port', 9050)
profile.set_preference("network.proxy.socks_remote_dns", False)
profile.update_preferences()
browser = webdriver.Firefox(firefox_profile= profile, executable_path=r'C:\Users\USER\Desktop\pythonLearning\kompassScriping\geckodriver.exe')
browser.get("http://check.torproject.org")


# In[14]:


path = "C:/Users/USER/Desktop/pythonLearning/kompassScriping"
config_relative_path(path)
countryPath = 'bg.kompass.com'
kompass_base_url = "https://%s" % countryPath
# browser= webdriver.Chrome('./chromedriver.exe')

openDirectory(countryPath)
df_loaded_html = None
try:
    df_loaded_html = pd.read_csv('./%s/loaded_html.csv' % countryPath)
except:
    df_loaded_html = pd.DataFrame({"url": [""],
                                    "saved_time": [""],
                                    "relative_directory": [""],
                                    "absolute_dir": [""],
                                  })


# In[7]:


# get all company category

html_home_page = openUrl(kompass_base_url)
category_links = get_all_category_links(html_home_page)
with open('./%s/category_links.json' % countryPath , 'w') as f:
    json.dump(category_links, f)


# In[6]:


#get all sub links

with open('./%s/category_links.json' % countryPath) as f:
    category_links = json.load(f)

sum_all_company = 0
for index, category_link in enumerate(category_links):
    print('iteration %s from %s' %(index, len(category_links)))
    print(category_link['link'])
    html_companies =  loadCompnyListHtml(kompass_base_url + category_link['link'])
    get_sub_links(html_companies, category_link)
    df_loaded_html.to_csv('./%s/loaded_html.csv' % countryPath)
    with open('./%s/category_links_with_sublinks.json' % countryPath , 'w') as f:
        json.dump(category_links, f)
print('sum all compny in %s is %s' %(countryPath ,sum_all_company))


# In[17]:


# get all companies list pages
df_loaded_html = pd.read_csv('./%s/loaded_html.csv' % countryPath)

for index, row in df_loaded_html.iterrows():
# for category_link in category_links:
    get_all_paginaiton(index, row)
print('done get all pages')
    


# In[8]:


# parse all company lists
csv_path = "./%s/companies_details.csv" % (countryPath)
try:
    df_compnies_details = pd.read_csv(csv_path)
except:
    df_compnies_details = pd.DataFrame()
    
for index, row in df_loaded_html.iterrows():
    parse_company_list_html(index, row, csv_path)
print('parse all company')
df_compnies_details.to_csv(csv_path)


# In[ ]:





# In[ ]:




