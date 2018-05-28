import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3
import time
import Crypto


#This API allows other clients to send this client a message
@cherrypy.expose
def receiveMessage(data):

    #Attempt to get the compulsory fields
    try:

        sender = data['sender']
        destination =  data['destination']
        message = data['message']
        stamp = data['stamp']

        #Check if message is encrypted
        encryption = data.get('encryption','0')


        if (encryption == '2'):
        	LOGIN_SERVER_PUBLIC_KEY = '41fb5b5ae4d57c5ee528adb078ac3b2e'
        	message = binascii.unhexlify(message)
        	iv = message[:16]
        	cipher = AES.new(LOGIN_SERVER_PUBLIC_KEY, AES.MODE_CBC, iv )
        	message = cipher.decrypt(message[16:]).rstrip(PADDING)

        #Prepare database for storing message    
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/messages.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

            
            
        cursor.execute("INSERT INTO Messages(Sender,Destination,Message,Stamp) VALUES (?,?,?,?)",[sender,destination,message,stamp])

        conn.commit()
        conn.close()

        return '0'

    except KeyError:

        return '1: Missing Compulsory Field'
        





#Calls the destination's /receiveMessage API to send a message to them
@cherrypy.expose
def sendMessage(message):


    #Check session
    try:
        sender = cherrypy.session['username']
        destination = cherrypy.session['chatTo']

        if (message == None or len(message) == 0):
            raise cherrypy.HTTPRedirect('/chat?userUPI='+destination)
        else :
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
            pingResponse = urllib2.urlopen("http://"+ip+":"+port+"/ping?sender="+str(sender)).read()

            #If destination was pinged successfully
            if (pingResponse == '0'):

                stamp = str(time.time())
                url = "http://"+ip+":"+port+"/receiveMessage"

                """BS = 16
                message = message + (BS - len(message) % BS) * chr(BS - len(message) % BS) 
            	iv = Random.new().read(AES.block_size)
            	cipher = AES.new('41fb5b5ae4d57c5ee528adb078ac3b2e', AES.MODE_CBC, iv)
            	message = base64.b64encode(iv + cipher.encrypt(message))"""

                output_dict = {'sender' :sender,'message':message,'stamp':stamp,'destination':destination,'encryption':'0'}  	
                data = json.dumps(output_dict) 

                req = urllib2.Request(url,data,{'Content-Type':'application/json'})

                response = urllib2.urlopen(req).read()
    	    
                if (response[0] == '0'):
                    #Keep them on chat page
                    saveMessage(message,sender,destination)
                    raise cherrypy.HTTPRedirect('/chat?otherUser='+destination)
                else:

                    print 'Code error : ' + response[0]
                    return 'Message not sent but ping response is 0'

    except KeyError:

        return 'Session expired'


@cherrypy.expose
def getChatPage(otherUser):

    #Check session
    try:
        username = cherrypy.session['username']
        #Serve chat page html
        workingDir = os.path.dirname(__file__)
        filename = workingDir + "/html/chatbox.html"
        f = open(filename,"r")
        page = f.read()
        f.close()
        cherrypy.session['chatTo'] = otherUser

        dbFilename = workingDir + "/db/messages.db"
        f = open(dbFilename,"r")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        cursor.execute("SELECT Message,Sender FROM Messages WHERE (Sender = ? AND Destination = ?) OR (Sender = ? AND Destination = ?) ORDER BY Stamp",[otherUser,username,username,otherUser])

        rows = cursor.fetchall()


        for row in rows:

            if (str(row[1]) == otherUser):
                page += '<div class = "chat friend">'
                page += '<div class = "user-photo" src = "/static/html/anon.png"></div>'
                page += '<p class = "chat-message">' + str(row[0]) + '</p>'
                page += '</div>'

            else:
                page += '<div class = "chat self">'
                page += '<div class = "user-photo" src = "/static/html/anon.png"></div>'
                page += '<p class = "chat-message">' + str(row[0]) + '</p>'
                page += '</div>'



        filename = workingDir + "/html/chatbox-bottom.html"
        f = open(filename,"r")
        page += f.read()
        f.close()


        return page

    except KeyError:

        return 'Session expired'


#Public Ping API for checking if this client is online
@cherrypy.expose
def ping(sender):

    return '0'

@cherrypy.expose
def saveMessage(message,sender,destination):


    workingDir = os.path.dirname(__file__)
    dbFilename = workingDir + "/db/messages.db"
    f = open(dbFilename,"r+")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()

    stamp = str(time.time())

    cursor.execute("INSERT INTO Messages(Sender,Destination,Message,Stamp) VALUES (?,?,?,?)",[sender,destination,message,stamp])

    conn.commit()
    conn.close()



@cherrypy.expose
def receiveFile(data):
	sender = data['sender']
	destination = data['destination']
	filee = data['file']
	filename = data['filename']
	content_type = data['content_type']
	stamp = str(time.time())
	
