import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3


def receiveMessage(sender,destination,message,encoding = None,encryption = None,hashing = None,hash = None,decryptionKey = None,groupID = None):

    #Check if user is logged in
    try:

        username = cherrypy.session['username']
        #Make sure that receiver is actually the person logged in
        if (username == destination):

            #Prepare database for storing message    
            workingDir = os.path.dirname(__file__)
            dbFilename = workingDir + "/db/messages.db"
            f = open(dbFilename,"r+")
            conn = sqlite3.connect(dbFilename)
            cursor = conn.cursor()

            #Search for existing user messages in database
            cursor.execute("SELECT Messages from Messaging WHERE UPI = ?",[sender])
            row = cursor.fetchall()
            #Insert user and their message if new, update if existing.
            if (len(row) == 0):

                cursor.execute("INSERT INTO Messaging(UPI,Messages) VALUES (?,?)",[sender,message])
            else:
                cursor.execute("UPDATE Messaging SET Messages = ? WHERE UPI = ?",[message,sender])

            conn.commit()
            conn.close()
            return ' DONE'

        else:
            return 2

    except KeyError:

        return 3

