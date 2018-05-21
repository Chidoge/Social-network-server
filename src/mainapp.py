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
import messageClass


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
        Page = "404 Error : Website not found"
        cherrypy.response.status = 404
        return Page


    #Index page
    @cherrypy.expose
    def index(self):

        #Serve main page html
        workingDir = os.path.dirname(__file__)
        filename = workingDir + "/html/index.html"
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
        

    #Login function
    @cherrypy.expose
    def login(self):

        #Check if user is logged in
        try:
            #If user is logged in, send them to the user page
            randomString = cherrypy.session['username']
            raise cherrypy.HTTPRedirect('/showUserPage')

        except KeyError: 
            #Get working directory to find html file
            workingDir = os.path.dirname(__file__)
            filename = workingDir + "/html/login.html"
            f = open(filename,"r")
            page = f.read()
            f.close()

        try:

            #Limit user to 3 password attempts
            attempts = cherrypy.session['attempts']

            if (attempts < 3):
                page += '</br><center><div style="color:red">Sorry, that username or password was incorrect. Please try again.</div></center>'
                page += '<center><div style="color:red">Attempts remaining : ' + str(3-attempts ) + '</div></center><br/>'

            else:
                raise cherrypy.HTTPRedirect('/')


        except KeyError:
            pass


        return page
    

    #Shows online users
    @cherrypy.expose
    def showOnlineUsers(self):

        #Check the user is logged in
        try :

            #Call API to check for other online users
            r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + cherrypy.session['username'] + "&password=" + cherrypy.session['password'])
            response = r.read()
            errorCode = response[0]

            #Split API response using white space as tokeniser
            users = response.split()

            #Prepare database for storing online users
            workingDir = os.path.dirname(__file__)
            dbFilename = workingDir + "/db/online_users.db"
            f = open(dbFilename,"r+")
            conn = sqlite3.connect(dbFilename)
            cursor = conn.cursor()

            #User list starts after 4th white space
            for i in range(5,len(users)) :

                userUPI= users[i].split(',')[0]
                userIP = users[i].split(',')[2]

                #Search for existing user in database
                cursor.execute("SELECT IP FROM OnlineUsers WHERE UPI = ?",[userUPI])
                row = cursor.fetchall()

                #Insert new user information if new,update existing user information
                if (len(row) == 0):
                    cursor.execute("INSERT INTO OnlineUsers(UPI,IP) VALUES (?,?)",[userUPI,userIP])
                else:
                    cursor.execute("UPDATE OnlineUsers SET IP = ? WHERE UPI = ?",[userIP,userUPI])


            conn.commit()
            conn.close()
            #If API was called successfully, show the users
            if (errorCode == '0') :
                page = response

            #Error message
            else :
                page = 'Oops! Something broke'

        #There is no username
        except KeyError :
            page = 'Session expired'

        return page


    #Profile page
    @cherrypy.expose
    def showUserPage(self):

        #Check if user is logged in before displaying
        try:
            #Do something with session username
            username = cherrypy.session['username']
            
            return profiles.showUserPage()

        #If not logged in and trying to access userpage, bring them back to the default page
        except KeyError:

            raise cherrypy.HTTPRedirect('/')

            


    #LOGGING IN AND OUT
    @cherrypy.expose
    def signin(self, username=None, password=None):

        #If text field was empty
        if (username == None and password == None):
            raise cherrypy.HTTPRedirect('/login')
        else:
            pass

        #Check their name and password and send them either to the main page, or back to the main login screen
        errorCode = self.authoriseUserLogin(username,password)

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
                    raise cherrypy.HTTPRedirect('/login')

            #First attempt
            except KeyError:
                cherrypy.session['attempts'] = 1
                raise cherrypy.HTTPRedirect('/login')



    @cherrypy.expose
    def signout(self):

        #Check if user is logged in
        try:
            username = cherrypy.session['username']
            hashedPW = cherrypy.session['password']

            #Call API to log off
            r = urllib2.urlopen("http://cs302.pythonanywhere.com/logoff?username=" + username + "&password=" + hashedPW + "&enc=0")
            response = r.read()

            #Successful log off
            if (response[0] == "0"):
                    cherrypy.lib.sessions.expire()
                    raise cherrypy.HTTPRedirect('/')

            #Error logging off
            else:
                raise cherrypy.HTTPRedirect('/')

        #If user isn't logged in, this method redirects user to main page
        except KeyError:
            raise cherrypy.HTTPRedirect('/')
    


    @cherrypy.expose
    def editProfile(self):

        #Check if user is logged in
        try:
            username = cherrypy.session['username']
            return profiles.editProfile(username)

        except KeyError:
            raise cherrypy.HTTPRedirect('/')



    @cherrypy.expose
    def saveEdit(self,name,position,description,location,picture):

        #Check if user is logged in
        try:
            username = cherrypy.session['username']
            profiles.saveEdit(username,name,position,description,location,picture)
            raise cherrypy.HTTPRedirect('/showUserPage')

        except KeyError:
            raise cherrypy.HTTPRedirect('/')
            

    @cherrypy.expose
    def receiveMessage(self,sender,destination,message,encoding = None,encryption = None,hashing = None,hash = None,decryptionKey = None,groupID = None):

        messageClass.receiveMessage(sender,destination,message,encoding,encryption,hashing,hash,decryptionKey,groupID)


    #Compares user typed hashed password with server hashed password.
    @cherrypy.expose
    def authoriseUserLogin(self,username,password):

        #Hash user's password
        hashedPW = hashlib.sha256(password+username).hexdigest()

        #Call API to request a log in.
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/report?username=" + username + "&password=" + hashedPW + "&ip=122.60.90.158&port=80&location=2")

        #Check if login was successful
        response = r.read()
        #If error code is 0, save the user, and return 0 to indicate successful login.
        if (response[0] == '0'):
            cherrypy.session['username'] = username
            cherrypy.session['password'] = hashedPW
            return 0
        else :
            return 1




@cherrypy.expose
def runMainApp():
    # Create an instance of MainApp and tell Cherrypy to send all requests under / to it. (ie all of them)
    cherrypy.tree.mount(MainApp(), "/")

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

#Run the function to start everything
runMainApp()
