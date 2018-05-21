import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3


def receiveMessage(sender,destination,message,encoding = None,encryption = None,hashing = None,hash = None,decryptionKey = None,groupID = None):

    #Prepare database for storing message    
    workingDir = os.path.dirname(__file__)
    dbFilename = workingDir + "/db/messages.db"
    f = open(dbFilename,"r+")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()

            #Search for existing user messages in database
    cursor.execute("SELECT Messages from Received WHERE UPI = ?",[sender])
    row = cursor.fetchone()
            #for r in rows:
                #print r
            #Insert user and their message if new, update if existing.
    if (len(row) == 0):

        cursor.execute("INSERT INTO Received(UPI,Messages) VALUES (?,?)",[sender,message])
    else:
        message = str(row[0]) + ',' + message
        cursor.execute("UPDATE Received SET Messages = ? WHERE UPI = ?",[message,sender])

    conn.commit()
    conn.close()

    return 'DONE'


