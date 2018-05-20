import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3

@cherrypy.expose
def showUserPage() :
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
    for row in rows :
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


@cherrypy.expose
def editProfile(username) :
    
    #Get working directory to find html and database file
    workingDir = os.path.dirname(__file__)

    #Read database
    dbFilename = workingDir + "/db/profiles.db"
    f = open(dbFilename,"r")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()
    cursor.execute("SELECT Name, Position, Description,Location,Picture FROM Profile WHERE username = ?" ,[username])

    row = cursor.fetchall()

    #Serve dynamic html content(show current user information, but let them replace with new information)
    page = '<head>'
    page += '<title>Edit My Profile</title>'          
    page += '</head>'
    page += '<body>'          
    page += '<h1><b> My Profile</b></h1><br/>'
    page += '<form action = "/saveEdit" method = "post">'            
    page += '<p>Name: <input type="text" name="name" value ="' + str(row[0][0]) + '">'
    page += '<p>Position: <input type="text" name="position" value ="' + str(row[0][1]) + '">'          
    page += '<p>Description: <input type="text" name="description" value ="' + str(row[0][2]) + '">'
    page += '<p>Location: <input type="text" name="location" value ="' + str(row[0][3]) + '">'          
    page += '<p>Picture: <input type="text" name="picture" value ="' + str(row[0][4]) + '">'   
    page += '<input type ="submit" value="Edit"/></form>'
    page += '</body>'

    return page

@cherrypy.expose
def saveEdit(username,name,position,description,location,picture) :
    
    #Get working directory to find html and database file
    workingDir = os.path.dirname(__file__)
    
    #Read database
    dbFilename = workingDir + "/db/profiles.db"
    f = open(dbFilename,"r+")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()

    for i in range (0,5) :
        if (i == 0):
    	   cursor.execute("UPDATE Profile SET " + 'Name = \'' + name +  "\' WHERE username = '" + username + "'")
        elif (i == 1):
            cursor.execute("UPDATE Profile SET " + 'Position = \'' + position +  "\' WHERE username = '" + username + "'")
        elif (i == 2):
            cursor.execute("UPDATE Profile SET " + 'Description = \'' + description +  "\' WHERE username = '" + username + "'")
        elif (i == 3):
            cursor.execute("UPDATE Profile SET " + 'Location = \'' + location +  "\' WHERE username = '" + username + "'")
        elif (i == 4):
            cursor.execute("UPDATE Profile SET " + 'Picture = \'' + picture +  "\' WHERE username = '" + username + "'")


    conn.commit()

    conn.close()

    

     

    
