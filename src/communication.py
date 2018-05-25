import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3
import time


#This API allows other clients to send this client a message
@cherrypy.expose
def receiveMessage(data):


    try:

        sender = data['sender']
        destination =  data['destination']
        message = data['message']
        stamp = data['stamp']

        #Prepare database for storing message    
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/messages.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        

        #Search for existing user messages in database
        cursor.execute("SELECT Messages from Received WHERE UPI = ?",[sender])

        row = cursor.fetchone()

        if (row == None):

            cursor.execute("INSERT INTO Received(UPI,Messages) VALUES (?,?)",[sender,message + ' Time: ' + stamp])
        else:
            message = str(row[0]) + '\n' + message + ' Time: ' + stamp
            cursor.execute("UPDATE Received SET Messages = ? WHERE UPI = ?",[message,sender])

        conn.commit()
        conn.close()
        return '0'
        
    except KeyError:

        return '1';




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
        pingResponse = urllib2.urlopen("http://"+ip+":"+port+"/ping?sender="+str(username)).read()

        #If destination was pinged successfully
        if (pingResponse == '0'):

            stamp = str(time.time())
            url = "http://"+ip+":"+port+"/receiveMessage"

            output_dict = {'sender' :username,'message':message,'stamp':stamp,'destination':destination}  	
            data = json.dumps(output_dict) 	
            req = urllib2.Request(url,data,{'Content-Type':'application/json'})

            response = urllib2.urlopen(req).read()
	    
            if (response[0] == '0'):
                #Keep them on chat page
                saveMessage(message,destination)
                raise cherrypy.HTTPRedirect('/chat?userUPI='+destination)
            else:
                return 'Message not sent but ping response is 0'

    except KeyError:

        return 'Session expired'


@cherrypy.expose
def getChatPage(userUPI):

    #Serve chat page html
    workingDir = os.path.dirname(__file__)
    filename = workingDir + "/html/chatbox.html"
    f = open(filename,"r")
    page = f.read()
    f.close()
    cherrypy.session['chatTo'] = userUPI

    dbFilename = workingDir + "/db/messages.db"
    f = open(dbFilename,"r")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()

    cursor.execute("SELECT Messages FROM Received WHERE UPI = ?",[userUPI])

    row = cursor.fetchall()

    page += '<div class = "chat self">'
    page += '<div class = "user-photo"></div>'
    page += '<p class = "chat-message">' + str(row[0]) + '</p>'
    page += '</div>'

    filename = workingDir + "/html/chatbox-bottom.html"
    f = open(filename,"r")
    page += f.read()
    f.close()


    return page


#Public Ping API for checking if this client is online
@cherrypy.expose
def ping(sender):

    return '0'

@cherrypy.expose
def saveMessage(message,destination):

    #Open database
    workingDir = os.path.dirname(__file__)
    dbFilename = workingDir + "/db/messages.db"
    f = open(dbFilename,"r+")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()

    cursor.execute("SELECT Messages FROM Sent WHERE UPI = ?",[destination])

    row = cursor.fetchone()

    stamp = str(time.time())
    message = message + ' Time : ' + stamp

    if (row == None):
        cursor.execute("INSERT INTO Sent(UPI,Messages) VALUES (?,?)",[destination,message + '\n'])
    else:
        cursor.execute("UPDATE Sent SET Messages = ? WHERE UPI = ?",[str(row[0]) + message +'\n',destination])

    conn.commit()
    conn.close()

@cherrypy.expose
def getPublicKey():
    pass
