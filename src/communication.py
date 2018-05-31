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

            
            
        cursor.execute("INSERT INTO Messages(Sender,Destination,Message,Stamp,isFile) VALUES (?,?,?,?,?)",[sender,destination,message,stamp,'0'])

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

                #Construct the URL for calling the /receiveFile API of the destination
                url = "http://%s:%s/receiveMessage" % (ip,port)

                #Put compulsory arguments into output dictionary, then json encode it
                stamp = str(time.time())
                output_dict = {'sender' :sender,'message':message,'stamp':stamp,'destination':destination}
                data = json.dumps(output_dict)

                try:
                    #Put json encoded object into http header
                    req = urllib2.Request(url,data,{'Content-Type':'application/json'})
                    response = urllib2.urlopen(req).read()

                    if (response[0] == '0'):
                        #Keep them on chat page
                        saveMessage(message,sender,destination,stamp,'0')
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
def saveMessage(message,sender,destination,stamp,isFile):

    #Prepare database for message storing
    workingDir = os.path.dirname(__file__)
    dbFilename = workingDir + "/db/messages.db"
    f = open(dbFilename,"r+")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()

    #Insert message row
    cursor.execute("INSERT INTO Messages(Sender,Destination,Message,Stamp,isFile) VALUES (?,?,?,?,?)",[sender,destination,message,stamp,isFile])
    
    #Save changes
    conn.commit()
    conn.close()


@cherrypy.expose
def sendFile(fileData):


    #Check user session
    try:

        sender = cherrypy.session['username']
        destination = cherrypy.session['destination']

        #Add a stamp to the file and use for file name
        stamp = str(int(time.time()))

        #Guess an extension for the file type
        extension = mimetypes.guess_extension(str(fileData.type),strict=True)

        #Prepare file path and store on server
        workingDir = os.path.dirname(__file__)
        newfilename = workingDir + "/serve/serverFiles/sent_files/" + sender + stamp + extension

        if fileData.file: 
            with file(newfilename, 'wb') as outfile:
                outfile.write(fileData.file.read())


        image = open(newfilename, 'rb')
        imageRead = image.read()
        #Encode image in base 64
        encodedFile = base64.b64encode(imageRead)

        #Get IP and PORT of destination
        data = users.getUserIP_PORT(destination)
        ip = data['ip']
        port = data['port']

        #Guess the mimetype of the file that we're sending
        content_type = mimetypes.guess_type(imageRead, strict=True)


        #Put compulsory arguments into output dictionary, then json encode it
        output_dict = {'sender' : sender,'destination' : destination,'file': encodedFile , 'filename' : sender+stamp+ extension ,'content_type' : content_type,'stamp' :stamp}
        data = json.dumps(output_dict)

        #Construct the URL for calling the /receiveFile API of the destination
        url = "http://%s:%s/receiveFile" % (ip,port)

        #Attempt to call the API, if fails, return error
        try:
            #Put json encoded object into http header
            req = urllib2.Request(url,data,{'Content-Type':'application/json'})
            response = urllib2.urlopen(req).read()
            saveMessage('/static/serverFiles/sent_files/'+sender+stamp+extension,sender,destination,stamp,'1')
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
    stamp = str(int(data['stamp']))

    #Open image for sending
    workingDir = os.path.dirname(__file__)

    filename = workingDir + "/serve/serverFiles/sent_files/" + str(filenameIn)
    decodedFile = base64.decodestring(fileIn)
    file = open(filename, 'wb')
    file.write(decodedFile)

    saveMessage('/static/serverFiles/sent_files/'+str(filenameIn),sender,destination,stamp,'1')
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
    row = cursor.fetchone()

    #Use anon picture if they dont have a picture
    if (row == None):

        picture = '/static/css/anon.png'

    elif (str(row[0]) == 'None'):

        picture = '/static/css/anon.png'
    else:
        picture = str(row[0])



    #Compile the chat history between sender and destination in order
    dbFilename = workingDir + "/db/messages.db"
    f = open(dbFilename,"r")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()
    cursor.execute("SELECT Message,Sender,isFile FROM Messages WHERE (Sender = ? AND Destination = ?) OR (Sender = ? AND Destination = ?) ORDER BY Stamp",[destination,sender,sender,destination])
    rows = cursor.fetchall()


    for row in rows:

        if (str(row[1]) == destination):
            page += '<div class = "chat friend">'
            page += '<div class = "user-photo"><img src = "'+picture+ '"></div>'
            if (str(row[2]) == '1'):
                page +=  addEmbeddedViewer(str(row[0]))
            else: 
                page += '<div class = "chat-message">' + str(row[0]) + '</div>'
            page += '</div>'

        else:
            page += '<div class = "chat self">'
            #page += '<div class = "user-photo"><img src = "'+picture+ '"></div>'
            if (str(row[2]) == '1'):
                page +=  addEmbeddedViewer(str(row[0]))
            else: 
                page += '<div class = "chat-message">' + str(row[0]) + '</div>'
            page += '</div>'


    page += '</div>'
    filename = workingDir + "/html/chatbox-bottom.html" 
    f = open(filename,"r")
    page += f.read()
    f.close

    return page   

@cherrypy.expose
def addEmbeddedViewer(fileSource):


    page = '<div class = "chat-message-image"><img src="' + fileSource + '">' +'</div>'

    return page


@cherrypy.expose
def acknowledge(data):

    try:
        sender = data['sender']
        stamp = data['stamp']
        hashingStandard = str(data['hashing'])
        dataHash = data['hash']

        if (hashingStandard == '0'):
            pass

    except KeyError:
        return '1 Missing Compulsory Field'

