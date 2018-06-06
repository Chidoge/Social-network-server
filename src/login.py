"""login.py

    COMPSYS302 - Software Design
    Author: Lincoln Choy
    
This file contains functions and API's which help with logging into the login server and
    authentication
"""

import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3
import socket
import thread
import threading
import time
import sys
import random
import smtplib
from MyThread import MyThread
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

listen_port = 10010

#Get user's ip address
#hostIP = urllib2.urlopen('https://api.ipify.org').read()
"""For internal ip address"""
hostIP =socket.gethostbyname(socket.gethostname())




"""This function checks if the login information provided by the user is valid
    Inputs : username (string)
            password (string)
            location (string)
    Output : None
    """
def sign_in(username,password,location):


    #Check their name and password and send them either to the main page, or back to the main login screen
    error_code = authorise_user_login(username,password,location)

    #Successful log in
    if (error_code == 0):
        raise cherrypy.HTTPRedirect('/two_fa_page')

    #Failed log in.
    else:
        raise cherrypy.HTTPRedirect('/')





"""This function logs the user off by calling the login server's /logout API
    Input : None
    Output : None
    """
def sign_out():

    #Check if user is logged in
    try:
        username = cherrypy.session['username']
        hashed_pw = cherrypy.session['password']

        thread.stop()

        #Call API to log off
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/logoff?username=" + username + "&password=" + hashed_pw + "&enc=0")
        response = r.read()

        #Successful log off
        if (response[0] == '0'):
            cherrypy.lib.sessions.expire()
            raise cherrypy.HTTPRedirect('/')

        #Error logging off
        else:
            raise cherrypy.HTTPRedirect('/')

    #If user isn't logged in, this method redirects user to main page
    except KeyError:
        raise cherrypy.HTTPRedirect('/')




"""This function calls the login server's /report API to validate user login information and to log them on
    Will return '0' if login is successful, '1' otherwise
    Inputs : username (string)
             password (string)
             location (string)
    Output : '0' or '1' (string)
    """
def authorise_user_login(username,password,location):



    #Hash user's password
    hashed_pw = hashlib.sha256(password+username).hexdigest()

    url = ("http://cs302.pythonanywhere.com/report?username=%s&password=%s&ip=%s&port=%s&location=%s" % (username,hashed_pw,hostIP,listen_port,location))
    #Call API to request a log in.
    r = urllib2.urlopen(url)

    #Check if login was successful
    response = r.read()

    #If error code is 0, save the user, and return 0 to indicate successful login.
    if (response[0] == '0'):

        cherrypy.session['temp_username'] = username
        cherrypy.session['temp_password'] = hashed_pw
        cherrypy.session['location'] = location
        code = generate_2fa_code()
        send_code(code,username)
        raise cherrypy.HTTPRedirect('/two_fa_page')
        return '0'
    else :
        return '1'



"""This function checks the 2fa code provided by the user
    Input : code (string)
    Output : None
    """
def check_code(code):

    try:

        tfa_code = cherrypy.session['code']
        if (tfa_code == code):

            username = cherrypy.session['temp_username']
            hashed_pw = cherrypy.session['temp_password']
            location = cherrypy.session['location']
            url = ("http://cs302.pythonanywhere.com/report?username=%s&password=%s&ip=%s&port=%s&location=%s" % (username,hashed_pw,hostIP,listen_port,location))

            cherrypy.session['username'] = username
            cherrypy.session['password'] = hashed_pw
            save_user(username,hashed_pw)
            #Start thread for reporting to login server (every 40 seconds)
            report_to_server(url)
            raise cherrypy.HTTPRedirect('/show_user_page')
        else:
            raise cherrypy.HTTPRedirect('/two_fa_page')

    except KeyError:

        return 'Session expired'





"""This function generates a code for 2 factor authentication
    Input : None
    Output : code (string)
    """
def generate_2fa_code():
    
    alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    code = ''
    for i in range(0,3):
        code += random.choice(alpha)
    for i in range(0,3):
        code += str(random.randint(0,9))

    cherrypy.session['code'] = code
    return code





"""This function sends the 2fa code to the user's university email
    Input : code (string)
    Output : None
    """
def send_code(code,username):

    email_user = '2effayycompsys302@gmail.com'
    email_send = ('%s@aucklanduni.ac.nz' % username)

    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_send
    msg['Subject'] = '2FA Code'

    body = ('Your code is %s' % code)

    msg.attach(MIMEText(body,'plain'))

    text = msg.as_string()
    server = smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    server.login(email_user,'throwlockeR123')

    server.sendmail(email_user,email_send,text)
    server.quit()





"""This function creates a global thread which is used to report to the login server
    while the application is open
    Input : url (string, url calls the login server's /report API to stay logged in)
    Output : None
    """
def report_to_server(url):

    global thread
    thread = MyThread()
    thread.daemon = True
    thread.set_login_URL(url)
    thread.start()





"""This function saves the login information of the current user to a text file,so
    that, when the program exits, there is semi-global information to call the /logoff API
    Inputs : username (string)
             hashed_pw (string)
    Output : None
    """
def save_user(username,hashed_pw):

    #Save the current user globally so we can log off at program exit
    working_dir = os.path.dirname(__file__)
    filename = working_dir + '/currentUser.txt'


    with open(filename, 'w') as file:
        file.write(username +";"+hashed_pw)

