import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3

# The address we listen for connections on
listen_ip = "0.0.0.0"
listen_port = 15010

#Login function
@cherrypy.expose
def login():
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


#LOGGING IN AND OUT
@cherrypy.expose
def signin(username=None, password=None):

    #If text field was empty
    if (username == None and password == None):
        raise cherrypy.HTTPRedirect('/login')
    else:
        pass

    #Check their name and password and send them either to the main page, or back to the main login screen
    errorCode = authoriseUserLogin(username,password)

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

#Log out API
@cherrypy.expose
def signout():

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


#Compares user typed hashed password with server hashed password.
@cherrypy.expose
def authoriseUserLogin(username,password):

    #Get user's ip address
    hostIP = urllib2.urlopen('https://api.ipify.org').read()

    #Hash user's password
    hashedPW = hashlib.sha256(password+username).hexdigest()
    string = "http://cs302.pythonanywhere.com/report?username=" + username + "&password=" + hashedPW + "&ip="+hostIP+"&port="+str(listen_port)+"&location=2"

    #Call API to request a log in.
    r = urllib2.urlopen("http://cs302.pythonanywhere.com/report?username=" + username + "&password=" + hashedPW + "&ip="+hostIP+"&port="+str(listen_port)+"&location=2")

    #Check if login was successful
    response = r.read()
    #If error code is 0, save the user, and return 0 to indicate successful login.
    if (response[0] == '0'):
        cherrypy.session['username'] = username
        cherrypy.session['password'] = hashedPW
        return 0
    else :
        return 1
