import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3


#Shows online users
@cherrypy.expose
def showOnlineUsers():

    try:
        username = cherrypy.session['username']
        #Prepare database for storing users
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/userlist.db"
        f = open(dbFilename,"r")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        #Call API to check for other online users
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + username + "&password=" + cherrypy.session['password'])
        response = r.read()

        #Split API response using white space as tokeniser
        users = response.split()

        #Start building html for showing online users
        page = '<h1>Online Users</h1>'

        #User list starts after 4th white space
        for i in range(5,len(users)) :

            userUPI= users[i].split(',')[0]

            if (userUPI != username):

                page += '<p>' + userUPI + '</p>'
                page += '<form action ="/viewProfile?userUPI=' + userUPI+'" method="post" enctype="multipart/form-data">'
                page += '<input type ="submit" value="View Profile"/></form>'
                page += '<form action ="/chat?userUPI=' + userUPI +'"method="post" enctype="multipart/form-data">'
                page += '<input type ="submit" value="Send Message"/></form>'

    except KeyError:

        return 'Session expired'

    return page



@cherrypy.expose
def saveOnlineUsers():

    try:
        username = cherrypy.session['username']
        #Call API to check for other online users
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + username + "&password=" + cherrypy.session['password'])
        response = r.read()
        errorCode = response[0]

        #Split API response using white space as tokeniser
        users = response.split()
            
        #Prepare database for storing online users
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/userlist.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        #User list starts after 4th white space
        for i in range(5,len(users)):

            userUPI= users[i].split(',')[0]
            userIP = users[i].split(',')[2]
            userPORT = users[i].split(',')[3]

            #Search for existing user in database
            cursor.execute("SELECT IP,PORT FROM UserList WHERE UPI = ?",[userUPI])
            row = cursor.fetchall()

            #Insert new user information if new,update existing user information
            if (len(row) == 0):
                cursor.execute("INSERT INTO UserList(UPI,IP,PORT) VALUES (?,?,?)",[userUPI,userIP,userPORT])
            else:
                cursor.execute("UPDATE UserList SET IP = ?,PORT = ? WHERE UPI = ?",[userIP,userPORT,userUPI])

        conn.commit()
        conn.close()

    except KeyError:

        return 'Session Expired'
