import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3
import mainapp

@cherrypy.expose
def editProfile() :
    
    #Get working directory to find html and database file
    workingDir = os.path.dirname(__file__)
    filename = workingDir + "/html/editprofile.html"
    f = open(filename,"r")
    page = f.read()
    f.close()
    return page

@cherrypy.expose
def saveEdit(name,position,description,location,picture) :
    
    #Get working directory to find html and database file
    workingDir = os.path.dirname(__file__)
            
    #Read database
    dbFilename = workingDir + "/db/profiles.db"
    f = open(dbFilename,"r")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()

    for i in range (1,5) :
    	
	cursor.execute("UPDATE Profile SET" + 'Position = ' + position +  "WHERE Name = 'Lincoln Choy' ")

    conn.commit()

    conn.close()

     

    
