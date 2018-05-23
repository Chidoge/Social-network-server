#!/usr/bin/python
""" cherrypy_example.py

    COMPSYS302 - Software Design
    Author: Lincoln Choy

    This program uses the CherryPy web server (from www.cherrypy.org).
"""
# Requires:  CherryPy 3.2.2  (www.cherrypy.org)
#            Python  (We use 2.7)

# The address we listen for connections on
listen_ip = "0.0.0.0"
listen_port = 15010

import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3
import socket

#Student defined files
import profiles
import communication
import users
import login


class MainApp(object):

    #CherryPy Configuration
    _cp_config = {'tools.encode.on': True, 
                  'tools.encode.encoding': 'utf-8',
                  'tools.sessions.on' : 'True',
                 }             

    #Catch 404 error
    @cherrypy.expose
    def default(self, *args, **kwargs):
        """The default page, given when we don't recognise where the request is for."""
        page = "404 Error : Website not found"
        cherrypy.response.status = 404
        return page


    #Index page
    @cherrypy.expose
    def index(self):

        #Serve main page html
        workingDir = os.path.dirname(__file__)
        filename = workingDir + "/html/login.html"
        f = open(filename,"r")
        page = f.read()
        f.close()
        #Check user is logged in
        try:
            username = cherrypy.session['username']
            raise cherrypy.HTTPRedirect('/showUserPage')

        #There is no username
        except KeyError:
            return page 
        
#------------------------------------------END-----------------------------------------#





#----------------------------------- LOGIN METHODS -------------------------------------#


    #LOGGING IN AND OUT
    @cherrypy.expose
    def signin(self, username=None, password=None):
        print username
        print password
        login.signin(username,password)


    #Log out API
    @cherrypy.expose
    def signout(self):

        login.signout()



    #Compares user typed hashed password with server hashed password.
    @cherrypy.expose
    def authoriseUserLogin(self,username,password):

        return login.authoriseUserLogin(username,password)


#-----------------------------------------END------------------------------------------#





#----------------------------------- PROFILE METHODS -----------------------------------#
    

    #Profile page
    @cherrypy.expose
    def showUserPage(self):
   
        return profiles.showUserPage()

        
    #Shows profile of user(userUPI)
    @cherrypy.expose
    def viewProfile(self,userUPI):

        return userUPI
        profiles.viewProfile(userUPI)


    #Lets user edit their own profile(returns page for editing profile)
    @cherrypy.expose
    def editProfile(self):

        return profiles.editProfile()


    #Helper function for editProfile(self)
    @cherrypy.expose
    def saveEdit(self,name,position,description,location,picture):

        profiles.saveEdit(name,position,description,location,picture)


    #Public API for other users to get this node's profile
    @cherrypy.expose
    def getProfile(self,profile_username,sender):

        return profiles.getProfile(profile_username,sender)

#----------------------------------------------END---------------------------------------#





#-----------------------------------OTHER CLIENT METHODS---------------------------------#
    
    #Returns the page that shows everyone who's online
    @cherrypy.expose
    def showOnlineUsers(self):

        users.saveOnlineUsers()
        return users.showOnlineUsers()

#-----------------------------------------END----------------------------------------------#





#-------------------------- COMMUNICATION(CLIENT-CLIENT) METHODS --------------------------#
    
    #Method for sending message(calls other clients receive message)
    @cherrypy.expose
    def sendMessage(self,message):

        communication.sendMessage(message)



    #Chat interface with a user
    @cherrypy.expose
    def chat(self,userUPI):

        return communication.getChatPage(userUPI)


    #Public Ping API for checking if this client is online
    @cherrypy.expose
    def ping(self,sender):

        return '0'


    #Public(Common) API for receiving message
    @cherrypy.expose
    def receiveMessage(self,sender,destination,message,encoding = None,encryption = None,hashing = None,hash = None,decryptionKey = None,groupID = None):

        return communication.receiveMessage(sender,destination,message,encoding,encryption,hashing,hash,decryptionKey,groupID)


#-------------------------------------------END--------------------------------------------#





#-------------------------------------RUNS THE SERVER--------------------------------------#

@cherrypy.expose
def runMainApp():

    conf = {

        '/static' : {
            'tools.staticdir.on'  : True,
            'tools.staticdir.dir' : os.path.dirname(__file__)
            
        }
    }

    # Create an instance of MainApp and tell Cherrypy to send all requests under / to it. (ie all of them)
    cherrypy.tree.mount(MainApp(), '/',conf)

    # Tell Cherrypy to listen for connections on the configured address and port.
    cherrypy.config.update({'server.socket_host': listen_ip,'server.socket_port': listen_port,'engine.autoreload.on': True,})

    print "========================="
    print "University of Auckland"
    print "COMPSYS302 - Software Design Application"
    print "========================================" 

    # Start the web server
    cherrypy.engine.start()
    # And stop doing anything else. Let the web server take over.
    cherrypy.engine.block()

#-------------------------------------------END---------------------------------------------------#

#Run the function to start everything
runMainApp()
