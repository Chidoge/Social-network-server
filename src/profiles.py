#!/usr/bin/python
""" This """
import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3
import socket
import users


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
        filename = workingDir + "/html/userpage.html"
        f = open(filename,"r")
        page = f.read()
        f.close()

        #Read database
        dbFilename = workingDir + "/db/profiles.db"
        f = open(dbFilename,"r")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()
        cursor.execute("SELECT Name, Position, Description,Location,Picture FROM Profile where username = ?",[username])

        rows = cursor.fetchall()

        name = rows[0][0]
        position = rows[0][1]
        description = rows[0][2]
        location = rows[0][3]
        picture = rows[0][4]


        #Call API to check for other online users
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + username + "&password=" + cherrypy.session['password'])
        response = r.read()

        #Split API response using white space as tokeniser
        users = response.split()


        #User list starts after 4th white space
        for i in range(5,len(users)) :

            userUPI= users[i].split(',')[0]

            #No need to show current user their own profile
            if (userUPI != username):
                page += '<p>' + userUPI + '</p>'
                page += '<form action ="/viewProfile?userUPI=' + userUPI+'" method="post">'
                page += '<button type ="submit">View Profile</button></form>'
                page += '<form action ="/chat?userUPI=' + userUPI +'"method="post">'
                page += '<button type ="submit">Send Message</button></form>'



        filename = workingDir + "/html/userpage-bottom.html"
        f = open(filename,"r")
        page += f.read()
        f.close

        page = page.replace("NAME_HERE",name)
        page = page.replace('POSITION_HERE',position)
        page = page.replace('DESCRIPTION_HERE',description)
        page = page.replace('LOCATION_HERE',location)
        page = page.replace('PICTURE_HERE',picture)




        return page 
    #If not logged in and trying to access userpage, bring them back to the default page
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
        dbFilename = workingDir + "/db/profiles.db"
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


#Call other node's getProfile
@cherrypy.expose
def viewProfile(userUPI):

    #Check session
    try:

        username = cherrypy.session['username']
        profile_username = userUPI
        #Open database
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/userlist.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        #Find ip and port - Should always exist, since this method is only called when this user is saved.
        cursor.execute("SELECT IP,PORT FROM UserList WHERE UPI = ?",[profile_username])
        row = cursor.fetchall()
        ip = str(row[0][0])
        port = str(row[0][1])

        #URL for requesting profile
        url = "http://"+ip+":"+port+"/getProfile"

        #Encode input arguments into json
        output_dict = {'sender' :username,'profile_username':profile_username}
        data = json.dumps(output_dict)  
        req = urllib2.Request(url,data,{'Content-Type':'application/json'})
        try :
            response = urllib2.urlopen(req,timeout= 3).read()
        except urllib2.URLError:
            raise cherrypy.HTTPRedirect('/chat?userUPI=dche192')
        
        print response

    except KeyError:

        return 'Session Expired'



@cherrypy.expose
def getProfile(data):

    profile_username = data['profile_username']
    sender = data['sender']

    workingDir = os.path.dirname(__file__) 
    #Read database
    dbFilename = workingDir + "/db/profiles.db"
    f = open(dbFilename,"r+")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor() 

    cursor.execute("SELECT Name,Position,Description,Location,Picture FROM Profile WHERE username = ?",[profile_username])

    row = cursor.fetchone()

    if (len(row) != 0):

        output_dict = {'Name' :row[0],'Position': row[1],'Description': row[2],'Location': row[3],'Picture': row[4]}
        data = json.dumps(output_dict)
        print data
        return data

    else:

        return '4'

    
     

    
