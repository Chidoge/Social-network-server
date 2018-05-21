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

    #Check the user is logged in
    try:

        #Call API to check for other online users
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + cherrypy.session['username'] + "&password=" + cherrypy.session['password'])
        response = r.read()
        errorCode = response[0]

        #Split API response using white space as tokeniser
        users = response.split()

        #Prepare database for storing online users
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/online_users.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        #User list starts after 4th white space
        for i in range(5,len(users)) :

            userUPI= users[i].split(',')[0]
            userIP = users[i].split(',')[2]
            userPORT = users[i].split(',')[3]

            #Search for existing user in database
            cursor.execute("SELECT IP,PORT FROM OnlineUsers WHERE UPI = ?",[userUPI])
            row = cursor.fetchall()

            #Insert new user information if new,update existing user information
            if (len(row) == 0):
                cursor.execute("INSERT INTO OnlineUsers(UPI,IP,PORT) VALUES (?,?,?)",[userUPI,userIP,userPORT])
            else:
                cursor.execute("UPDATE OnlineUsers SET IP = ?,PORT = ? WHERE UPI = ?",[userIP,userPORT,userUPI])


        conn.commit()
        conn.close()
        #If API was called successfully, show the users
        if (errorCode == '0') :
            page = response

        #Error message
        else :
            page = 'Oops! Something broke'

    #There is no username
    except KeyError :
        page = 'Session expired'

    return page

