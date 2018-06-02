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
listen_port = 10010

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
        filename = workingDir + "./html/login.html"
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
    def signin(self, username=None, password=None,location=None):

        login.signin(username,password,location)


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

        users.saveOnlineUsers()
        return users.showUserPage()


    @cherrypy.expose
    def refreshUserList(self):

        return users.refreshUserList()


    @cherrypy.expose
    def chatUser(self,destination):

        users.setNewChatUser(destination)
     

    #Shows profile of user(userUPI)
    @cherrypy.expose
    def viewProfile(self,destination):

        return profiles.viewProfile(destination)


    @cherrypy.expose
    def viewOwnProfile(self):

        return profiles.viewOwnProfile()


    #Saves user changes to their profile
    @cherrypy.expose
    def saveEdit(self,name,position,description,location):

        profiles.saveEdit(name,position,description,location)


    #Change user's profile picture
    @cherrypy.expose
    def editPicture(self,picture):

        profiles.editPicture(picture)

    #Public API for other users to get this node's profile
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def getProfile(self):

        data = cherrypy.request.json
        return profiles.getProfile(data)

#----------------------------------------------END---------------------------------------#





#-----------------------------------OTHER CLIENT METHODS---------------------------------#
    

#Nothing here at the moment
    @cherrypy.expose
    def refreshChat(self):

        return communication.refreshChat()

#-----------------------------------------END----------------------------------------------#





#-------------------------- COMMUNICATION(CLIENT-CLIENT) METHODS --------------------------#
    

    #Public Ping API for checking if this client is online
    @cherrypy.expose
    def ping(self,sender):

        return '0'


    #Calls other node's /receiveMessage API
    @cherrypy.expose
    def sendMessage(self,message):

        #Makes sure user isn't just sending nothing
        messageNoSpaces = message.replace(" ","")
        if (len(messageNoSpaces) != 0):
            return communication.sendMessage(message)
        else:
            raise cherrypy.HTTPRedirect('/showUserPage')

    @cherrypy.expose
    def setMessageDisplayed(self):

        cherrypy.session['newMessage'] = False


    #Calls other node's /receiveFile API
    @cherrypy.expose
    def sendFile(self,fileData):
        if (fileData != ''):
            return communication.sendFile(fileData)
        else:
            raise cherrypy.HTTPRedirect('/showUserPage')


    #Public(Common) API for receiving message
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveMessage(self):

        data = cherrypy.request.json
        return communication.receiveMessage(data)


    #Public(Common) API for receiving files
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveFile(self):

        data = cherrypy.request.json
        return communication.receiveFile(data)


#-------------------------------------------END--------------------------------------------#





#-------------------------------------RUNS THE SERVER--------------------------------------#

@cherrypy.expose
def runMainApp():

    if (len(os.path.dirname(__file__)) != 0 ):
        conf = {

            '/static' : {
                'tools.staticdir.on'  : True,
                'tools.staticdir.dir' : os.path.dirname(__file__) + "/serve"
                
            }
        }
    else :
        conf = {

            '/static' : {
                'tools.staticdir.on'  : True,
                'tools.staticdir.dir' : os.getcwd() +"/serve"
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
