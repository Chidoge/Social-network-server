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
from MyThread import MyThread

listen_port = 10010



#LOGGING IN AND OUT
@cherrypy.expose
def signin(username=None, password=None,location=None):

    #If text field was empty
    if (username == None and password == None):
        raise cherrypy.HTTPRedirect('/')
    else:
        pass

    #Check their name and password and send them either to the main page, or back to the main login screen
    errorCode = authoriseUserLogin(username,password,location)

    #Successful log in
    if (errorCode == 0):
        raise cherrypy.HTTPRedirect('/showUserPage')

    #Failed log in.
    else:
        raise cherrypy.HTTPRedirect('/')
        

#Log out API
@cherrypy.expose
def signout():

    #Check if user is logged in
    try:
        username = cherrypy.session['username']
        hashedPW = cherrypy.session['password']
        thread.stop()
        #Call API to log off
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/logoff?username=" + username + "&password=" + hashedPW + "&enc=0")
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


#Compares user typed hashed password with server hashed password.
@cherrypy.expose
def authoriseUserLogin(username,password,location):

    #Get user's ip address
    hostIP = urllib2.urlopen('https://api.ipify.org').read()
    """For internal ip address"""
    #hostIP =socket.gethostbyname(socket.gethostname())

    #Hash user's password
    hashedPW = hashlib.sha256(password+username).hexdigest()

    url = "http://cs302.pythonanywhere.com/report?username=" + username + "&password=" + hashedPW + "&ip="+hostIP+"&port="+str(listen_port)+"&location="+location
    #Call API to request a log in.
    r = urllib2.urlopen("http://cs302.pythonanywhere.com/report?username=" + username + "&password=" + hashedPW + "&ip="+hostIP+"&port="+str(listen_port)+"&location="+location)

    #Check if login was successful
    response = r.read()

    #If error code is 0, save the user, and return 0 to indicate successful login.
    if (response[0] == '0'):

        cherrypy.session['username'] = username
        cherrypy.session['password'] = hashedPW
        saveUser(username,hashedPW)
        
        reportToServer(url)

        return '0'
    else :
        return '1'


def reportToServer(url):

    global thread
    thread = MyThread()
    thread.daemon = True
    thread.setURL(url)
    thread.start()

def saveUser(username,hashedPW):

    #Save the current user globally so we can log off at program exit
    workingDir = os.path.dirname(__file__)
    filename = workingDir + '/currentUser.txt'


    with open(filename, 'w') as file:
        file.write(username +";"+hashedPW)

