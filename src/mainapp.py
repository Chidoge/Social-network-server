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
listen_port = 1234

import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3
import profiles

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
        Page = f.read()
        f.close()

        #Try to access username key, if empty, session is expired and should give user option to login.
        try:
            randomString = cherrypy.session['username']
            raise cherrypy.HTTPRedirect('/showUserPage')

        #There is no username
        except KeyError :
            return Page 
        
    

    @cherrypy.expose
    def login(self):

        #Check if user is logged in
        try:
            #If user is logged in, send them to the user page
            randomString = cherrypy.session['username']
            raise cherrypy.HTTPRedirect('/showUserPage')

        except KeyError : 

            #Get working directory to find html file
            workingDir = os.path.dirname(__file__)
            filename = workingDir + "/html/login.html"
            f = open(filename,"r")
            Page = f.read()
            f.close()

        try :
            
            #Limit user to 3 password attempts
            attempts = cherrypy.session['attempts']

            if (attempts < 3) :
                Page += '</br><center><div style="color:red">Sorry, that username or password was incorrect. Please try again.</div></center>'
                Page += '<center><div style="color:red">Attempts remaining : ' + str(3-attempts ) + '</div></center><br/>'
            else :
                raise cherrypy.HTTPRedirect('/')

        except KeyError :
            pass


        return Page
    

    @cherrypy.expose
    def showOnlineUsers(self):

        #Try block - In case the user session is expired somehow
        try:

            r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + cherrypy.session['username'] + "&password=" + cherrypy.session['password'])
            response = r.read()
            errorCode = response[0]
            
            if (errorCode == '0'):
                Page = response
            else :
                Page = 'Oops! Something broke'

        #There is no username
        except KeyError :

            Page = 'Session expired'

        return Page

    #Profile page
    @cherrypy.expose
    def showUserPage(self) :

        #Check if user is logged in before displaying
        try:

            
            #Do something with session username
            username = cherrypy.session['username']
            
            #Get working directory to find html and database file
            workingDir = os.path.dirname(__file__)
            
            #Serve html to page
            filename = workingDir + "/html/userpage.html"
            f = open(filename,"r")
            page = f.read()
            f.close()

            #Read database
            dbFilename = workingDir + "/db/profiles.db"
            f = open(dbFilename,"r")
            conn = sqlite3.connect(dbFilename)
            cursor = conn.cursor()
            cursor.execute("SELECT Name, Position, Description,Location,Picture FROM Profile")

            rows = cursor.fetchall()

            #Show info
            for row in rows:
                for col in range (0,4) :
                    if (col == 0) :
                        page += ('</br><b>Profile</b></br>')
                        page += ('Name : ' +str(row[col]) + '</br>')
                    elif (col == 1) :
                        page += ('Position : ' +str(row[col]) + '</br>')
                    elif (col == 2) :
                        page += ('Description : ' +str(row[col]) + '</br>')
                    elif (col == 3) :
                        page += ('Location : ' +str(row[col]) + '</br>')
                    elif (col == 4) :
                        page += ('Picture : ' +str(row[col]) + '</br>')

            return page    

        #If not logged in and trying to access userpage, bring them back to the default page
        except KeyError :

            raise cherrypy.HTTPRedirect('/')

            


    #LOGGING IN AND OUT
    @cherrypy.expose
    def signin(self, username=None, password=None):

        if (username == None and password == None) :
            raise cherrypy.HTTPRedirect('/login')
        else :
            pass

        #Check their name and password and send them either to the main page, or back to the main login screen
        errorCode = self.authoriseUserLogin(username,password)

        if (errorCode == 0) :
            raise cherrypy.HTTPRedirect('/showUserPage')
        else :
            #If failed password attempts exist,limit attempts to 3 then lock user out(currently only sends user back to index).
            try :
                attempts = cherrypy.session['attempts']
                if (attempts >= 3 ):
                    raise cherrypy.HTTPRedirect('/')
                else:
                    cherrypy.session['attempts'] = attempts + 1
                    raise cherrypy.HTTPRedirect('/login')
            #First attempt
            except KeyError :
                cherrypy.session['attempts'] = 1
                raise cherrypy.HTTPRedirect('/login')



    @cherrypy.expose
    def signout(self):
        """Logs the current user out, expires their session"""
        username = cherrypy.session.get('username')
        try :
            username = cherrypy.session['username']
            hashedPW = cherrypy.session['password']
            print username
            print hashedPW
            r = urllib2.urlopen("http://cs302.pythonanywhere.com/logoff?username=" + username + "&password=" + hashedPW + "&enc=0")
            response = r.read()
            print response
        
            if (response[0] == "0") :
                    cherrypy.lib.sessions.expire()
                    raise cherrypy.HTTPRedirect('/')
            else :
                raise cherrypy.HTTPRedirect('/')
        except KeyError:
            raise cherrypy.HTTPRedirect('/')
    
    @cherrypy.expose
    def editProfile(self) :

        return profiles.editProfile()

    @cherrypy.expose
    def saveEdit(self,name,position,description,location,picture):

        profiles.saveEdit(name,position,description,location,picture)

    #Compares user typed hashed password with server hashed password.
    @cherrypy.expose
    def authoriseUserLogin(self,username,password):

        hashedPW = hashlib.sha256(password+username).hexdigest()

        r = urllib2.urlopen("http://cs302.pythonanywhere.com/report?username=" + username + "&password=" + hashedPW + "&ip=122.60.90.158&port=80&location=2")
        response = r.read()
        print username
        print password

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
