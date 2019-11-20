# -*- coding: utf-8 -*-

import datetime, requests, os, time, random, re, smtplib, ssl
from bs4 import BeautifulSoup
from selenium import webdriver
from pymongo import MongoClient
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import credentials

cd = credentials.GetCredentials('passwordARNL.kdbx', os.environ['PASSWORD'])

def sendingEmails(newEvents, db):
    # Sendding Email
    sender_email = cd.emailUsername()
    password = cd.emailPassword()

    # Try to log in to server and send email
    try:
        emailRecords = db.users
        emailList = [x['email'] for x in emailRecords.find({})]
        message = MIMEMultipart("alternative")
        message["Subject"] = "Les nouveaux évènements sur Artistik Rezo Club !"
        message["From"] = sender_email
        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            for receiver_email in emailList:
                message["To"] = receiver_email
                print("-- Sending email to {}".format(receiver_email))
                # Create the plain-text and HTML version of your message
                html = """\
                <html>
                  <body>
                    <p>Bonjour, bonjour !</p>
                    <p>Voici les nouveaux évènements sur <a href="http://www.clubartistikrezo.com/mon-compte"> Artistik Rezo Club</a> :</p>
                """
                totalEvent = 0
                for event in newEvents:
                    html += """<b style="font-family:arial;font-size:115%;">""" + event['title'] + """ - </b>"""
                    html += """<i style="font-family:arial">"""+ event['date'] + """</i>"""
                    html += """<p style="font-family:arial">""" + event['description']
                    html += """ <a href=\""""+event["linkArtistikRezo"]+""""\">Plus d\'infos sur artistik rezo </a></p>"""
                    totalEvent += 1
                html += """
                    <br><p style="font-family:arial">Voilà pour les nouveaux évènement du jour. 
                    A demain si de nouveaux évènements arrivent !<br><br>
                    Si vous ne voulez plus recevoir la newsletter, envoyez moi un mail en cliquant
                    <a href="mailto:jthillar@student.42.fr?subject=Désabonnement%20Newsletter%20Atritik%20Rezo">ici</a>
                  </body>
                </html>
                """

                # Turn these into plain/html MIMEText objects
                part1 = MIMEText(html, "html")

                # Add HTML/plain-text parts to MIMEMultipart message
                # The email client will try to render the last part first
                message.attach(part1)
                server.sendmail(sender_email, receiver_email, message.as_string())

    except Exception as e:
        # Print any error messages to stdout
        print(e)


def artistikRezoJob():

    print('--> Connect to Mongo...')
    client = MongoClient("mongodb+srv://" + cd.mongoDbUsername() + ":" + cd.mongoDbPassword() + cd.mongoDbUrl())
    db = client.get_database('artistik_rezo')

    newRecords = db.days_records
    oldRecords = db.old_records

    oldEvents = list()
    oldRecordsVec = oldRecords.find({})
    for e in oldRecordsVec:
        e.pop('updated', None)
        e.pop('_id', None)
        oldEvents.append(e)

    url = 'http://www.clubartistikrezo.com/'

    print('--> Getting info from artistik rezo...')
    #Set Up Driver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ['GOOGLE_CHROME_SHIM']
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(url)

        mailName = 'signin[username]'
        driver.find_element_by_name(mailName).send_keys(cd.artistikRezoUsername())
        time.sleep(1. + random.random())

        passwordName = 'signin[password]'
        driver.find_element_by_name(passwordName).send_keys(cd.artistikRezoPassword())
        time.sleep(1. + random.random())

        submitButtonClass = 'connexion'
        driver.find_element_by_name(submitButtonClass).click()
        time.sleep(1. + random.random())

        urlBase = 'http://www.clubartistikrezo.com/evenements?page='
        newEvents = list()

        html = driver.execute_script("return document.documentElement.outerHTML;")
        soup2 = BeautifulSoup(html)
        pages = soup2.find('div', {'class': 'pager'})
        if pages is not None:
            pagesRef = pages.find_all('a')
            pageTotal = 1 if len(pagesRef) == 0 else len(pagesRef) - 2

        now = datetime.datetime.now()

        for i in range(1, pageTotal):

            url = urlBase + str(i)

            r = driver.get(url)
            html = driver.execute_script("return document.documentElement.outerHTML;")
            soup = BeautifulSoup(html, features='lxml')

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

                            if eventInfo not in oldEvents:
                                eventInfo['updated'] = now
                                oldRecords.insert_one(eventInfo)
                                del eventInfo["_id"]
                                del eventInfo["updated"]
                                newEvents.append(eventInfo)

        resultDict = dict(updated=now)
        if len(newEvents) > 0:
            print('--> Sending emails...')
            resultDict['newEvents']=newEvents
            newRecords.insert_one(resultDict)
            sendingEmails(newEvents, db)
        else:
            print('<- No New events.')

    except Exception as e:
        print("Error when getting infos : {}".format(repr(e)))

    finally:
        driver.close()
        print('<-- Daily Job endend.')


if __name__ == "__main__":
    artistikRezoJob()