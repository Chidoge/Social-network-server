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

        raise cherrypy.HTTPRedirect('/showUserPage')
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

            #Get IP and PORT of destination
            data = users.getUserIP_PORT(destination)
            ip = data['ip']
            port = data['port']

            try:
                #Ping destination to see if they are online
                url = "http://%s:%s/ping?sender=%s" % (ip,port,sender)
                pingResponse = urllib2.urlopen(url).read()

            except urllib2.URLError, exception:
                return 'Could not ping'


            #If destination was pinged successfully
            if (pingResponse == '0'):

                #Put compulsory arguments into output dictionary, then json encode it
                stamp = str(time.time())
                output_dict = {'sender' :sender,'message':message,'stamp':stamp,'destination':destination}
                data = json.dumps(output_dict)

                #Construct the URL for calling the /receiveFile API of the destination
                url = "http://%s:%s/receiveMessage" % (ip,port)

                try:
                    #Put json encoded object into http header
                    req = urllib2.Request(url,data,{'Content-Type':'application/json'})
                    response = urllib2.urlopen(req).read()

                    if (response[0] == '0'):
                        #Keep them on chat page
                        saveMessage(message,sender,destination)
                        raise cherrypy.HTTPRedirect('/showUserPage')
                    else:

                        print 'Code error : ' + response[0]
                        return 'Message not sent but ping response is 0'


                except urllib2.URLError, exception:

                    return 'Message could not be sent'


    except KeyError:

        return 'Session expired'


#Function which locally stores the messages being sent by current user
@cherrypy.expose
def saveMessage(message,sender,destination):

    #Prepare database for message storing
    workingDir = os.path.dirname(__file__)
    dbFilename = workingDir + "/db/messages.db"
    f = open(dbFilename,"r+")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()

    #Create stamp
    stamp = str(time.time())

    #Insert message row
    cursor.execute("INSERT INTO Messages(Sender,Destination,Message,Stamp) VALUES (?,?,?,?)",[sender,destination,message,stamp])
    
    #Save changes
    conn.commit()
    conn.close()


@cherrypy.expose
def sendFile(filename):


    #Check user session
    try:
        sender = cherrypy.session['username']
        destination = cherrypy.session['destination']

        #Open image for sending
        workingDir = os.path.dirname(__file__)
        newfilename = workingDir + "/serve/serverFiles/" + str(filename)
        image = open(newfilename, 'rb')
        imageRead = image.read()

        #Encode image in base 64
        encodedFile = base64.b64encode(imageRead)

        #Get IP and PORT of destination
        data = users.getUserIP_PORT(destination)
        ip = data['ip']
        port = data['port']

        #Guess the mimetype of the file that we're sending
        content_type = mimetypes.guess_type(newfilename, strict=True)

        #Add a stamp to the file
        stamp = str(time.time())

        #Put compulsory arguments into output dictionary, then json encode it
        output_dict = {'sender' : sender,'destination' : destination,'file': encodedFile , 'filename' : filename ,'content_type' : content_type,'stamp' :stamp}
        data = json.dumps(output_dict)

        #Construct the URL for calling the /receiveFile API of the destination
        url = "http://%s:%s/receiveFile" % (ip,port)

        #Attempt to call the API, if fails, return error
        try:
            #Put json encoded object into http header
            req = urllib2.Request(url,data,{'Content-Type':'application/json'})
            response = urllib2.urlopen(req).read()
            raise cherrypy.HTTPRedirect('/')

        except urllib2.URLError, exception:

            return 'File could not be sent'


    except KeyError:

        raise cherrypy.HTTPRedirect('/')


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


@cherrypy.expose
def getChatPage(page,sender,destination):

    #Add chat divisions to page
    workingDir = os.path.dirname(__file__)
    filename = workingDir + "/html/chatbox.html"
    f = open(filename,"r")
    page += f.read()
    f.close
    page += '<div id = "chatlogs" class="chatlogs">'

    #Grab profile picture of destination to put into chat box
    dbFilename = workingDir + "/db/userinfo.db"
    f = open(dbFilename,"r")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()
    cursor.execute("SELECT Picture FROM Profile WHERE UPI = ?",[destination])
    row = cursor.fetchall()

    #Use anon picture if they dont have a picture
    if (len(row) != 0):
        picture = str(row[0][0])
    else:
        picture = '/static/css/anon.png'


    #Compile the chat history between sender and destination in order
    dbFilename = workingDir + "/db/messages.db"
    f = open(dbFilename,"r")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()
    cursor.execute("SELECT Message,Sender FROM Messages WHERE (Sender = ? AND Destination = ?) OR (Sender = ? AND Destination = ?) ORDER BY Stamp",[destination,sender,sender,destination])
    rows = cursor.fetchall()


    for row in rows:

        if (str(row[1]) == destination):
            page += '<div class = "chat friend">'
            page += '<div class = "user-photo"><img src = "'+picture+ '"></div>'
            page += '<div class = "chat-message">' + str(row[0]) + '</div>'
            page += '</div>'

        else:
            page += '<div class = "chat self">'
            #page += '<div class = "user-photo"><img src = "'+picture+ '"></div>'
            page += '<div class = "chat-message">' + str(row[0]) + '</div>'
            page += '</div>'


    page += '</div>'
    filename = workingDir + "/html/chatbox-bottom.html"
    f = open(filename,"r")
    page += f.read()
    f.close

    return page   

