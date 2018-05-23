""" This """
import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3


#Shows main page after login
@cherrypy.expose
def showUserPage():

    #Check if user is logged in before displaying
    try:
        #Do something with session username
        username = cherrypy.session['username']
        #Get working directory to find html and database file
        workingDir = os.path.dirname(__file__)
                
        #Serve html to page
        filename = workingDir + "./html/userpage.html"
        f = open(filename,"r")
        page = f.read()
        f.close()

        #Read database
        dbFilename = workingDir + "./db/profiles.db"
        f = open(dbFilename,"r")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()
        cursor.execute("SELECT Name, Position, Description,Location,Picture FROM Profile where username = ?",[username])

        rows = cursor.fetchall()


        #Show info
        for row in rows:
            for col in range (0,4):
                if (col == 0) :
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
    except KeyError:

        raise cherrypy.HTTPRedirect('/')   

#Brings user to profile edit page
@cherrypy.expose
def editProfile():

    #Check if user is logged in
    try:
        username = cherrypy.session['username']    
        #Get working directory to find html and database file
        workingDir = os.path.dirname(__file__)

        #Read database
        dbFilename = workingDir + "./db/profiles.db"
        f = open(dbFilename,"r")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()
        cursor.execute("SELECT Name, Position, Description,Location,Picture FROM Profile WHERE username = ?" ,[username])

        row = cursor.fetchall()
        filename = workingDir + "./html/editprofile.html"
        f = open(filename,"r")
        page = f.read()

        #Serve dynamic html content(show current user information, but let them replace with new information)           
        page += '<label for="username"><h3>Username</h3></label>'
        page += '<input type="text" name="name" value ="' + str(row[0][0]) + '">'
        page += '<label for="position"><h3>Position</h3></label>'
        page += '<input type="text" name="position" value ="' + str(row[0][1]) + '">'   
        page += '<label for="description"><h3>Description</h3></label>'       
        page += '<input type="text" name="description" value ="' + str(row[0][2]) + '">'
        page += '<label for="location"><h3>Location</h3></label>' 
        page += '<input type="text" name="location" value ="' + str(row[0][3]) + '">'
        page += '<label for="Picture"><h3>Picture</h3></label>'          
        page += '<input type="text" name="picture" value ="' + str(row[0][4]) + '">'   
        page += '</br><button type="submit">Edit</button></form>'
        page += '</body>'

        return page

    except KeyError:
        raise cherrypy.HTTPRedirect('/')



@cherrypy.expose
def saveEdit(name=None,position=None,description=None,location=None,picture=None):
    
    #Check if user is logged in
    try:

        username = cherrypy.session['username']    
        #Get working directory to find html and database file
        workingDir = os.path.dirname(__file__)
        
        #Read database
        dbFilename = workingDir + "./db/profiles.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        cursor.execute("UPDATE Profile SET Name = ?,Position =?,Description = ?,Location = ? WHERE username = ?",[name,position,description,location,username])
        
        #Save database changes and return user to userpage
        conn.commit()
        conn.close()
        raise cherrypy.HTTPRedirect('/showUserPage')

    except KeyError:

        raise cherrypy.HTTPRedirect('/')

@cherrypy.expose
def viewProfile(userUPI):

    #call other node's getProfile
    pass

@cherrypy.expose
def getProfile(profile_username,sender):


    return data
     

    
