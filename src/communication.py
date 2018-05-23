import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3


#This API allows other clients to send this client a message
@cherrypy.expose
def receiveMessage(sender,destination,message,stamp = None,encoding = None,encryption = None,hashing = None,hash = None,decryptionKey = None,groupID = None):

    #Prepare database for storing message    
    workingDir = os.path.dirname(__file__)
    dbFilename = workingDir + "/db/messages.db"
    f = open(dbFilename,"r+")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()


    #Search for existing user messages in database
    cursor.execute("SELECT Messages from Received WHERE UPI = ?",[sender])
    row = cursor.fetchone()

    if (len(row) == 0):

        cursor.execute("INSERT INTO Received(UPI,Messages) VALUES (?,?)",[sender,message])
    else:
        message = str(row[0]) + '\n' + message
        cursor.execute("UPDATE Received SET Messages = ? WHERE UPI = ?",[message,sender])

    conn.commit()
    conn.close()

    return '0'


#Calls the destination's /receiveMessage API to send a message to them
@cherrypy.expose
def sendMessage(message):

    #Check session
    try:
        username = cherrypy.session['username']
        destination = cherrypy.session['chatTo']

        #Check database for the destination's ip and port

        #Open database
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/userlist.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        #Find ip and port - Should always exist, since this method is only called when this user is saved.
        cursor.execute("SELECT IP,PORT FROM UserList WHERE UPI = ?",[destination])
        row = cursor.fetchall()
        ip = str(row[0][0])
        port = str(row[0][1])

        #Ping destination to see if they are online
        #pingResponse = urllib2.urlopen("http://"+ip+":"+port+"/ping?sender="+str(username)).read()

        #If destination was pinged successfully
        #if (pingResponse == '0'):
            #print 'SameEEEEEEEEE'
        response = urllib2.urlopen("http://"+localhost+":"+port+"/receiveMessage?sender="+username+"&destination="+destination+"&message="+str(message)).read()
        #if (response[0] == '0'):
            #return 'Message sent'

        #Keep them on chat page
        raise cherrypy.HTTPRedirect('/chat?userUPI='+destination)

    except KeyError:

        return 'Session expired'


@cherrypy.expose
def getChatPage(userUPI):

    #Serve chat page html
    workingDir = os.path.dirname(__file__)
    filename = workingDir + "/html/chat.html"
    f = open(filename,"r")
    page = f.read()
    f.close()
    cherrypy.session['chatTo'] = userUPI
    return page


#Public Ping API for checking if this client is online
@cherrypy.expose
def ping(sender):

    return '0'


@cherrypy.expose
def getPublicKey():
    pass