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

    #Read database
    dbFilename = workingDir + "/db/profiles.db"
    f = open(dbFilename,"r")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()
    cursor.execute("SELECT Name, Position, Description,Location,Picture FROM Profile WHERE ID = 1")

    row = cursor.fetchall()

  
    #Serve dynamic html content
    page = '<head>'
    page += '<title>Edit My Profile</title>'          
    page += '</head>'
    page += '<body>'          
    page += '<h1><b> My Profile</b></h1><br/>'
    page += '<form action = "/saveEdit" method = "post">'            
    page += '<p>Name: <input type="text" name="name" value =' + str(row[0][0]) + '>'
    page += '<p>Position: <input type="text" name="position" value =' + str(row[0][1]) + '>'          
    page += '<p>Description: <input type="text" name="description" value =' + str(row[0][2]) + '>'
    page += '<p>Location: <input type="text" name="location" value =' + str(row[0][3]) + '>'          
    page += '<p>Picture: <input type="text" name="picture" value =' + str(row[0][4]) + '>'   
    page += '<input type ="submit" value="Edit"/></form>'     
    page += '</body>'

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

    

     

    
