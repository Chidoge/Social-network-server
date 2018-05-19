import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3

@cherrypy.expose
def editProfile() :
    
    #Get working directory to find html and database file
    workingDir = os.path.dirname(__file__)
    pos = 0
    filename = workingDir + "/html/editprofile.html"
    f = open(filename,"r")

    #Serve dynamic html content
    page = '<head>'
    page += '<title>Edit My Profile</title>'          
    page += '</head>'
    page += '<body>'            
    page += '<b> My profile </b><br/>'
    page += '<form action = "/saveEdit" method = "post">'            
    page += '<p>Name: <input type="text" name="name"/>'
    page += '<p>Position: <input type="text" name="position" value = "Same"/>'          
    page += '<p>Description: <input type="text" name="description" value = "What"/>'
    page += '<p>Location: <input type="text" name="location" value/>'            
    page += '<p>Picture: <input type="text" name="picture"/>'    
    page += '<input type ="submit" value="Edit"/></form>'     
    page += '</body>'
    f.close()
    return page

@cherrypy.expose
def saveEdit(name,position,description,location,picture) :
    
    #Get working directory to find html and database file
    workingDir = os.path.dirname(__file__)
    
    #Read database
    dbFilename = workingDir + "/db/profiles.db"
    f = open(dbFilename,"r+")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()
    #cursor.execute("UPDATE Profile SET Position = 'Doctor' WHERE Name = 'Lincoln Choy' ")

    for i in range (1,5) :
        #print ("UPDATE Profile SET " + "Position = " + position +  " WHERE Name = 'Lincoln Choy' ")
        if (i == 1):
    	   cursor.execute("UPDATE Profile SET " + 'Name = \'' + name +  "\' WHERE ID = '1' ")
        elif (i == 2):
            cursor.execute("UPDATE Profile SET " + 'Position = \'' + position +  "\' WHERE ID = '1' ")
        elif (i == 3):
            cursor.execute("UPDATE Profile SET " + 'Description = \'' + description +  "\' WHERE ID = '1' ")
        elif (i == 4):
            cursor.execute("UPDATE Profile SET " + 'Location = \'' + location +  "\' WHERE ID = '1' ")
        elif (i == 5):
            cursor.execute("UPDATE Profile SET " + 'Picture = \'' + picture +  "\' WHERE ID = '1' ")


    conn.commit()

    conn.close()

    return "1"

     

    
