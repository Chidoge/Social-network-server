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

listen_port = 10005



gUser = ""
gPW = ""
gIP = ""
gloc = ""

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
        #If failed password attempts exist,limit attempts to 3 then lock user out(currently only sends user back to index).
        try:
            attempts = cherrypy.session['attempts']

            if (attempts >= 3 ):
                raise cherrypy.HTTPRedirect('/')

            else:
                cherrypy.session['attempts'] = attempts + 1
                raise cherrypy.HTTPRedirect('/')

        #First attempt
        except KeyError:
            cherrypy.session['attempts'] = 1
            raise cherrypy.HTTPRedirect('/')

#Log out API
@cherrypy.expose
def signout():

    #Check if user is logged in
    try:
        username = cherrypy.session['username']
        hashedPW = cherrypy.session['password']

        threading.Thread.daemon = True
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
    #hostIP = urllib2.urlopen('https://api.ipify.org').read()
    """For internal ip address"""
    hostIP =socket.gethostbyname(socket.gethostname())

    #Hash user's password
    hashedPW = hashlib.sha256(password+username).hexdigest()

    #Call API to request a log in.
    r = urllib2.urlopen("http://cs302.pythonanywhere.com/report?username=" + username + "&password=" + hashedPW + "&ip="+hostIP+"&port="+str(listen_port)+"&location="+location)

    #Check if login was successful
    response = r.read()

    #If error code is 0, save the user, and return 0 to indicate successful login.
    if (response[0] == '0'):

        cherrypy.session['username'] = username
        cherrypy.session['password'] = hashedPW

        global gUser,gPW,gIP,gloc

        gUser = username
        gPW = hashedPW
        gIP = hostIP
        gloc = location
        
        startThread()

        return 0
    else :
        return 1





def startThread():

    threading.Timer(40,reportToServer).start()

   

def reportToServer():


    threading.Timer(40, reportToServer).start()

    hostIP = urllib2.urlopen('https://api.ipify.org').read()

    r = urllib2.urlopen("http://cs302.pythonanywhere.com/report?username=" + gUser + "&password=" + gPW + "&ip="+gIP+"&port="+str(listen_port)+"&location="+gloc).read()

    print r
    

