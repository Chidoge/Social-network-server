#!/usr/bin/python
""" mainapp.py

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
import atexit
import sys

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
        working_dir = os.path.dirname(__file__)
        filename = working_dir + "./html/login.html"
        with open (filename,'r') as file:
            page = file.read()
            file.close()

        #Check user is logged in
        try:
            username = cherrypy.session['username']
            raise cherrypy.HTTPRedirect('/show_user_page')

        #There is no username
        except KeyError:
            return page 
        
#------------------------------------------END-----------------------------------------#





#----------------------------------- LOGIN METHODS -------------------------------------#


    #LOGGING IN AND OUT
    @cherrypy.expose
    def sign_in(self, username, password,location):

        login.sign_in(username,password,location)


    #Log out API
    @cherrypy.expose
    def sign_out(self):

        login.sign_out()


    @cherrypy.expose
    def check_code(self,code):

        login.check_code(code)

    @cherrypy.expose
    def two_fa_page(self):
        
        try:
            username = cherrypy.session['username']
            raise cherrypy.HTTPRedirect('/')

        except KeyError:
            
            #2FA page html
            working_dir = os.path.dirname(__file__)
            filename = working_dir + "./html/2fa.html"
            with open (filename,'r') as file:
                page = file.read()
                file.close()

            return page


    @cherrypy.expose
    def check_code(self,code):

        return login.check_code(code)




#-----------------------------------------END------------------------------------------#





#----------------------------------- PROFILE METHODS -----------------------------------#
    

    #Profile page
    @cherrypy.expose
    def show_user_page(self):

        users.save_online_users()
        return users.show_user_page()


    @cherrypy.expose
    def refresh_user_list(self):

        return users.refresh_user_list()


    @cherrypy.expose
    def chat_user(self,destination):

        users.set_new_chat_user(destination)
     

    #Shows profile of user(userUPI)
    @cherrypy.expose
    def view_profile(self,destination):

        return profiles.view_profile(destination)


    @cherrypy.expose
    def view_own_profile(self):

        return profiles.view_own_profile()


    #Saves user changes to their profile
    @cherrypy.expose
    def save_edit(self,name,position,description,location):

        profiles.save_edit(name,position,description,location)


    #Change user's profile picture
    @cherrypy.expose
    def edit_picture(self,picture):

        profiles.edit_picture(picture)

    #Public API for other users to get this node's profile
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def getProfile(self):

        data = cherrypy.request.json
        return profiles.get_profile(data)

#----------------------------------------------END---------------------------------------#





#-----------------------------------OTHER CLIENT METHODS---------------------------------#
    


    @cherrypy.expose
    def refresh_chat(self):

        return communication.refresh_chat()


    @cherrypy.expose
    def notify(self):

        return communication.notify()

    @cherrypy.expose
    def empty_buffer(self):
	

	destination = cherrypy.session['destination']
	communication.empty_buffer(destination)


#-----------------------------------------END----------------------------------------------#





#-------------------------- COMMUNICATION(CLIENT-CLIENT) METHODS --------------------------#
    

    #Public Ping API for checking if this client is online
    @cherrypy.expose
    def ping(self,sender):

        return communication.ping(sender)


    #Calls other node's /receiveMessage API
    @cherrypy.expose
    def send_message(self,message):

        #Makes sure user isn't just sending nothing
        message_no_spaces = message.replace(" ","")
        if (len(message_no_spaces) != 0):
            return communication.send_message(message)
        else:
            raise cherrypy.HTTPRedirect('/show_user_page')


    #Calls other node's /receiveFile API
    @cherrypy.tools.json_in()
    @cherrypy.expose
    def send_file(self):

        data = cherrypy.request.json
        file_data = data['file_data']
        mime_type = data['mime_type']
        communication.send_file(file_data,mime_type)


    #Public(Common) API for receiving message
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveMessage(self):

        data = cherrypy.request.json
        return communication.receive_message(data)


    #Public(Common) API for receiving files
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveFile(self):

        data = cherrypy.request.json
        return communication.receive_file(data)


#-------------------------------------------END--------------------------------------------#





#-------------------------------------RUNS THE SERVER--------------------------------------#

#Log off when exiting
def exit_handler():

    filename = textPath + '/currentUser.txt'
    with open (filename,'r') as file:
        info = file.read()
        info = info.split(";")
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/logoff?username=" + info[0] + "&password=" + info[1] + "&enc=0")
        file.close()


@cherrypy.expose
def runMainApp():

    if (len(os.path.dirname(__file__)) != 0 ):
        global textPath
        textPath = os.path.dirname(__file__)
        conf = {

            '/static' : {
                'tools.staticdir.on'  : True,
                'tools.staticdir.dir' : os.path.dirname(__file__) + "/serve"
                
            }
        }
    else :
        global textPath
        textPath = os.getcwd()
        conf = {

            '/static' : {
                'tools.staticdir.on'  : True,
                'tools.staticdir.dir' : os.getcwd() +"/serve"
            }
        }
    
    atexit.register(exit_handler)
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

atexit.register(exit_handler)
