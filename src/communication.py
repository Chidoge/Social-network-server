import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3
import time
import Crypto
import requests
import base64
import users

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
        destination = cherrypy.session['destination']

        if (message == None or len(message) == 0):

            raise cherrypy.HTTPRedirect('/chatUser?destination='+destination)

        else :
            
            data = users.getUserIP_PORT(destination)

            ip = data['ip']
            port = data['port']

            #Ping destination to see if they are online
            url = "http://%s:%s/ping?sender=%s" % (ip,port,sender)
            pingResponse = urllib2.urlopen(url).read()

            #If destination was pinged successfully
            if (pingResponse == '0'):

                stamp = str(time.time())

                url = "http://%s:%s/receiveMessage" % (ip,port)

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
                    raise cherrypy.HTTPRedirect('/showUserPage')
                else:

                    print 'Code error : ' + response[0]
                    return 'Message not sent but ping response is 0'

    except KeyError:

        return 'Session expired'


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
def sendFile(filename):

    #Check for user session
    try:
        sender = cherrypy.session['username']
        destination = cherrypy.session['destination']

        #Open image for sending
        workingDir = os.path.dirname(__file__)
        print 'FIle: ' + str(filename)
        newfilename = workingDir + "/serve/serverFiles/" + str(filename)
        img = open(newfilename, 'rb')

        read = img.read()

        data = users.getUserIP_PORT(destination)
        ip = data['ip']
        port = data['port']

        encodedFile = base64.b64encode(read)

        stamp = str(time.time())
        output_dict = {'sender' : sender,'destination' : destination,'file': encodedFile , 'filename' : filename ,'content_type' : 'image/jpg','stamp' :stamp}
        data = json.dumps(output_dict)


        url = "http://%s:%s/receiveFile" % (ip,port)
        print url
        try:
            req = urllib2.Request(url,data,{'Content-Type':'application/json'})
            response = urllib2.urlopen(req).read()

            raise cherrypy.HTTPRedirect('/')

        except urllib2.URLError, exception:
            return 'File could not be sent'

    except KeyError:
        return 'Session Expired'


@cherrypy.expose
def receiveFile(data):

    workingDir = os.path.dirname(__file__)
    sender = data['sender']
    destination = data['destination']
    fileIn = data['file']
    filenameIn = data['filename']
    content_type = data['content_type']
    stamp = str(data['stamp'])
    print 'sender : ' + sender

    #Open image for sending
    workingDir = os.path.dirname(__file__)

    filename = workingDir + "/serve/serverFiles/" + str(filenameIn)

    decodedFile = base64.decodestring(fileIn)
    file = open(filename, 'wb')
    file.write(decodedFile)

    return '0'

	
