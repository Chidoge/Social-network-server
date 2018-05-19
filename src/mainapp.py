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
import requests
import json
import hashlib
import mimetypes
import os

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
            raise cherrypy.HTTPRedirect('/userPage')

        #There is no username
        except KeyError :
           
            Page += "Click here to <a href='login'>login</a>."

        return Page
    

    @cherrypy.expose
    def login(self):

        #Check if user is logged in
        try:
            #Do something with session username
            randomString = cherrypy.session['username']
            raise cherrypy.HTTPRedirect('/userPage')

        except KeyError :

            Page = '<form action ="/signin" method="post" enctype="multipart/form-data">'

            try :
        		attempts = cherrypy.session['attempts']

        		if (attempts < 3) :
        			Page += '<div style="color:red">Sorry, that username or password was incorrect. Please try again.</div><br/>'
        			Page += ('<div style="color:red">Attempts remaining : ' + str(3-attempts ) + '</div><br/>')
        		else :
        			raise cherrypy.HTTPRedirect('/')

            except KeyError :
            	pass
            	
            Page += 'Username: <input type="text" name="username"/><br/>'
            Page += 'Password: <input type="password" name="password"/>'
            Page += '<input type ="submit" value="Login"/></form>'

            return Page
    

    @cherrypy.expose
    def showOnlineUsers(self):

        #Try block - In case the user session is expired somehow
        try:

            r = requests.get("http://cs302.pythonanywhere.com/getList?username=" + cherrypy.session['username'] + "&password=" + cherrypy.session['password'])
            errorCode = (r.text)[0]
            
            if (errorCode == '0'):
                Page = r.text
            else :
                Page = 'Oops! Something broke'

        #There is no username
        except KeyError :

            Page = 'Session expired'

        return Page

    #Profile page
    @cherrypy.expose
    def userPage(self) :

        #Check if user is logged in before displaying
        try:

            #Do something with session username
            username = cherrypy.session['username']

            #Get working directory to find html file
            workingDir = os.path.dirname(__file__)
            filename = workingDir + "/html/userpage.html"

            #cherrypy.response.headers['Content-Type'] = mimetypes.guess_type('.html')[0]

            #Serve html to page
            f = open(filename,"r")
            data = f.read()
            f.close()
            data += '<br/>'
            data += '<form action = "/showOnlineUsers" method = "post">'
            data += '<input type ="submit" value="See who\'s online"/></form>'
            data += '<form action = "/signout" method = "post">'
            data += '<input type ="submit" value="Sign out"/></form>'
            return data    

        #If not logged in and trying to access userpage, bring them back to the default page
        except KeyError :

            raise cherrypy.HTTPRedirect('/')

            


    #LOGGING IN AND OUT
    @cherrypy.expose
    def signin(self, username=None, password=None):

        #Check their name and password and send them either to the main page, or back to the main login screen
        errorCode = self.authoriseUserLogin(username,password)

        if (errorCode == 0) :
            raise cherrypy.HTTPRedirect('/userPage')
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
        if (username == None):
            pass
        else:
            cherrypy.lib.sessions.expire()
        raise cherrypy.HTTPRedirect('/')
    

    #Compares user typed hashed password with server hashed password.
    @cherrypy.expose
    def authoriseUserLogin(self,username,password):

        hashedPW = hashlib.sha256(password+username).hexdigest()

        r = requests.get("http://cs302.pythonanywhere.com/report?username=" + username + "&password=" + hashedPW + "&ip=122.60.90.158&port=80&location=2")
        print username
        print password
        string = r.text
        print string
        if (string[0] == '0'):
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
