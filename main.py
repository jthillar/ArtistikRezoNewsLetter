# -*- coding: utf-8 -*-

import datetime, os, time, random, re, smtplib, ssl
import credentials
import warnings

from pymongo import MongoClient
from bs4 import BeautifulSoup
from selenium import webdriver
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

cd = credentials.GetCredentials('passwordARNL.kdbx', os.environ['PASSWORD'])

warnings.filterwarnings("ignore")

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
            # Create the plain-text and HTML version of your message
            html = """\
            <html>
              <body>
                <div class="body" style="border: 3px solid #D10C09; border-radius: 12px; padding: 5%;margin:auto">
                    <a  href="http://www.clubartistikrezo.com/">
                        <img src="http://www.clubartistikrezo.com/images/logo.png" width="200" 
                        style="margin-bottom:6%;margin-left: auto; margin-right: auto; display: block;">
                    </a>
                    <div style="font-family:arial;font-size:108%;margin-bottom:3%;">
                        <p>Bonjour, </p>
                        <p>Voici les nouveaux évènements sur 
                            <a style="text-decoration : none; color : #D10C09; font-weight: bold;" 
                            href="http://www.clubartistikrezo.com/mon-compte"> Artistik Rezo Club</a> :
                        </p>
                    </div>
                    
            """
            totalEvent = 0
            for event in newEvents:
                html += """<div class="event" style="margin-bottom:4%;">"""
                html += """<div class="title" style="margin-bottom: 2%;">"""
                html += """<b style="font-family:arial;font-size:115%;">""" + event['title'] + """ - </b>"""
                if 'date' in event:
                    html += """<i style="font-family:arial">""" + event['date'] + """</i>"""
                html += """</div>"""
                html += """<div class="infos" style="display:flex;align-items:center;">"""
                if 'imgUrl' in event:
                    html += """<img style="float: left;margin-right: 15px;" alt=\"""" + event['title'] + """\" src=\"""" + event['imgUrl'] + """\" width="60">"""
                html += """<p style="font-family:arial;text-align:justify;">""" + event['description'] + """ """
                if 'linkArtistikRezo' in event:
                    html += """<a style="text-decoration : none; color : #D10C09; font-weight: bold;" href=\""""+event["linkArtistikRezo"] + """"\">Plus d\'infos sur Artistik Rezo.</a></p>"""
                html += """</div>"""
                html += """</div>"""
                totalEvent += 1
            html += """
                <p style="font-family:arial">Voilà pour les nouveaux évènements du jour. 
                A demain si de nouveaux évènements arrivent !<br><br>
                Si vous ne voulez plus recevoir la newsletter, vous pouvez 
                <a style="text-decoration : none; color : #D10C09; font-weight: bold;"
                 href="https://artistikrezoclub-newsletter.herokuapp.com/unregister/">vous désinscrire ici.</a>
                </div>
              </body>
            </html>
            """

            # Turn these into plain/html MIMEText objects
            part1 = MIMEText(html, "html")

            # Add HTML/plain-text parts to MIMEMultipart message
            # The email client will try to render the last part first
            message.attach(part1)
            for receiver_email in emailList:
                print("-- Sending email to {}".format(receiver_email))
                if "To" in message:
                    del message["To"]
                message["To"] = receiver_email
                server.sendmail(sender_email, receiver_email, message.as_string())

    except Exception as e:
        # Print any error messages to stdout
        print("Error when writing email : {}".format(repr(e)))


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
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('window-size=1920x1080')
        chrome_options.binary_location = os.environ['GOOGLE_CHROME_SHIM']
        driver = webdriver.Chrome(options=chrome_options)
    except:
        driver = webdriver.Chrome(executable_path=cd.chromeDriverExecutablePath())

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
            driver.get(url)

            html = driver.execute_script("return document.documentElement.outerHTML;")
            soup = BeautifulSoup(html, features='lxml')

            body = soup.find('div', {'class':'content'})

            if body is not None:

                events = body.find_all('div', {'class': re.compile('^item clearfix')})
                if events is not None:
                    for event in events:
                        eventInfo = dict()
                        title = event.find('h2')
                        image = event.find('img')
                        if image is not None:
                            eventInfo['imgUrl'] = 'http://www.clubartistikrezo.com' + image['src']
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
