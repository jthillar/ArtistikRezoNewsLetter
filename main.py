# -*- coding: utf-8 -*-

import re
import datetime, requests, os, time, random
from bs4 import BeautifulSoup
from selenium import webdriver

from pymongo import MongoClient


client = MongoClient("mongodb://julien:bctB1iR4@data-collection-l1mqp.mongodb.net/test?retryWrites=true&w=majority")
db = client.get_database('artistik_rezo')

records = db.days_records

url = 'http://www.clubartistikrezo.com/'
chromeExecutable = os.path.join(os.path.dirname(__file__))

r = requests.get(url)
html = r.content
soup = BeautifulSoup(html)
driver = webdriver.Chrome(executable_path='/Users/Julien/PycharmProjects/artistik_Rezo_alert/venv/bin/chromedriver')
driver.get(url)

mailName = 'signin[username]'
driver.find_element_by_name(mailName).send_keys('jthillar@student.42.fr')
time.sleep(1. + random.random())

passwordName = 'signin[password]'
driver.find_element_by_name(passwordName).send_keys('julien')
time.sleep(1. + random.random())

submitButtonClass = 'connexion'
driver.find_element_by_name(submitButtonClass).click()
time.sleep(1. + random.random())

urlBase = 'http://www.clubartistikrezo.com/evenements?page='
result = list()

html = driver.execute_script("return document.documentElement.outerHTML;")
soup2 = BeautifulSoup(html)
pages = soup2.find('div', {'class': 'pager'})
if pages is not None:
    pagesRef = pages.find_all('a')
    pageTotal = 1 if len(pagesRef) == 0 else len(pagesRef) - 2

for i in range(1, pageTotal):

    url = urlBase + str(i)

    r = driver.get(url)
    html = driver.execute_script("return document.documentElement.outerHTML;")
    soup = BeautifulSoup(html)

    body = soup.find('div', {'class':'content'})

    if body is not None:

        events = body.find_all('div', {'class': re.compile('^item clearfix')})
        if events is not None:
            for event in events:
                eventInfo = dict()
                title = event.find('h2')
                date = event.find('div', {'class':'date'})
                description = event.find('div', {'class':'desc'})
                if title is not None and description is not None and date is not None:
                    eventInfo['title'] = title.text
                    eventInfo['date'] = date.text.strip()
                    mapsTag = description.find('h3')
                    if mapsTag is not None:
                        mapsLink = mapsTag.find('a')
                        if mapsLink is not None:
                            eventInfo['mapsLink'] = mapsLink['href']
                    desc = description.find_all('p')
                    if len(desc) > 0:
                        descriptionText = ""
                        for p in desc:
                            linkTemp = p.find('a')
                            if linkTemp is not None:
                                if 'artistikrezo' in linkTemp['href']:
                                    eventInfo['linkArtistikRezo'] = linkTemp['href']
                                else:
                                    eventInfo['eventType'] = p.text.strip().split('.')[0]
                            else:
                                descriptionText += p.text.strip()

                        eventInfo['description'] = descriptionText

                    result.append(eventInfo)


    resultDict = dict(updated=datetime.datetime.now(), events=result)

records.insert_one(resultDict)
print(resultDict)