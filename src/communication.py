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
def receiveMessage(data):

    #Attempt to get the compulsory fields
    try:

        sender = data['sender']
        destination =  data['destination']
        message = data['message']
        stamp = data['stamp']

        #Check if message is encrypted
        encryption = data.get('encryption','0')

        #Does not support encryption
        if (encryption != '0'):
            return '9'

        #Prepare database for storing message    
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/messages.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        #Store the message into database
        cursor.execute("INSERT INTO Messages(Sender,Destination,Message,Stamp,isFile) VALUES (?,?,?,?,?)",[sender,destination,message,stamp,'0'])
        cursor.execute("INSERT INTO MessageBuffer(Sender,Destination,Message,Stamp,isFile) VALUES (?,?,?,?,?)",[sender,destination,message,stamp,'0'])
        #Save changes and return 0
        conn.commit()
        conn.close()


        return '0'

    #Missing compulsory field
    except KeyError:
        return '1'


#Calls the destination's /receiveMessage API to send a message to them
def sendMessage(message):

    #Check session
    try:

        sender = cherrypy.session['username']
        destination = cherrypy.session['destination']

        #Make sure user is typing in a message(cannot just be blank spaces)
        if (message == None or len(message) == 0):
            pass

        else :
            #Get IP and PORT of destination
            data = users.getUserIP_PORT(destination)
            ip = data['ip']
            port = data['port']


            #Check destination is online
            try:
                #Ping destination to see if they are online
                url = "http://%s:%s/ping?sender=%s" % (ip,port,sender)
                pingResponse = urllib2.urlopen(url,timeout=2).read()

                #Show error if ping response is invalid
                if (len(pingResponse) == 0 or pingResponse[0] != '0'):
                    users.logError("/sendMessage to %s failed | Reason : Ping response was not 0, Response : %s" % (destination,pingResponse))
                    return

            except urllib2.URLError, exception:
                users.logError("/sendMessage to %s failed | Reason : URL Error at /ping, Exception : %s" % (destination,exception))
                return

            #Construct the URL for calling the /receiveMessage API of the destination
            url = "http://%s:%s/receiveMessage" % (ip,port)

            #Put compulsory arguments into output dictionary, then json encode it
            stamp = str(time.time())
            output_dict = {'sender' :sender,'message':message,'stamp':stamp,'destination':destination}
            data = json.dumps(output_dict)

            try:
                #Put json encoded object into http request
                req = urllib2.Request(url,data,{'Content-Type':'application/json'})
                response = urllib2.urlopen(req).read()

                if (len(response) != 0 and response[0] == '0'):
                    saveMessage(message,sender,destination,stamp,'0')
                    return
                else:
                    users.logError("/sendMessage to %s failed | Reason : /receiveMessage response was not 0, Response : %s" % (destination,response))
                    return

            except urllib2.URLError, exception:
                users.logError("/sendMessage to %s failed | Reason : URL Error at /receiveMessage, Exception : %s" % (destination,exception))
                return


    except KeyError:

        raise cherrypy.HTTPRedirect('/')



#Function which locally stores the messages being sent by current user
def saveMessage(message,sender,destination,stamp,isFile):

    #Prepare database for message storing
    workingDir = os.path.dirname(__file__)
    dbFilename = workingDir + "/db/messages.db"
    f = open(dbFilename,"r+")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()

    #Insert message row
    cursor.execute("INSERT INTO Messages(Sender,Destination,Message,Stamp,isFile) VALUES (?,?,?,?,?)",[sender,destination,message,stamp,isFile])
    cursor.execute("INSERT INTO MessageBuffer(Sender,Destination,Message,Stamp,isFile) VALUES (?,?,?,?,?)",[sender,destination,message,stamp,isFile])

    #Save changes
    conn.commit()
    conn.close()



#Used to send a file which is uploaded using html file upload
def sendFile(fileData,mime_type):


    #Check user session
    try:

        sender = cherrypy.session['username']
        destination = cherrypy.session['destination']

        #Add a stamp to the file and use it for the file name
        stamp = str(int(time.time()))

        #Guess an extension for the file type
        extension = mimetypes.guess_extension(str(mime_type),strict=True)

        #Prepare file path to store on server
        workingDir = os.path.dirname(__file__)
        newfilename = workingDir + "/serve/serverFiles/sent_files/" + sender + stamp + extension

        #Store the file locally
        decodedFile = base64.decodestring(fileData)
        file = open(newfilename,"wb")
        file.write(decodedFile)
        file.close()

        #fileData is passed in as base 64
        encodedFile = fileData

        #Get IP and PORT of destination
        data = users.getUserIP_PORT(destination)
        ip = data['ip']
        port = data['port']

        #Check if user is online
        try:
            #Ping destination to see if they are online
            url = "http://%s:%s/ping?sender=%s" % (ip,port,sender)
            pingResponse = urllib2.urlopen(url,timeout=2).read()

            #Show error just in case destination didn't implement ping properly
            if (len(pingResponse) == 0 or pingResponse[0] != '0'):
                users.logError("/sendFile to %s failed | Reason : Ping response was not 0, Response : %s" % (destination,pingResponse))
                return

        except urllib2.URLError, exception:
            users.logError("/sendFile to %s failed | Reason : URL Error at /ping, Exception : %s" % (destination,exception))
            return


        #Put compulsory arguments into output dictionary, then json encode it
        output_dict = {'sender' : sender,'destination' : destination,'file': encodedFile , 'filename' : sender + stamp + extension ,'content_type' : mime_type,'stamp' :stamp}
        data = json.dumps(output_dict)

        #Construct the URL for calling the /receiveFile API of the destination
        url = "http://%s:%s/receiveFile" % (ip,port)

        #Attempt to call the API
        try:

            #Put json encoded object into http header
            req = urllib2.Request(url,data,{'Content-Type':'application/json'})
            response = urllib2.urlopen(req).read()

           
            #Make sure they are returning something(for interaction with substandard clients)
            if (len(response) !=0 or response[0] == '0'):

                saveMessage('/static/serverFiles/sent_files/'+sender+stamp+extension,sender,destination,stamp,'1')
                return
            else:
                users.logError("/sendFile to %s failed | Reason : /receiveFile response was not 0, Response : %s" % (destination,response))
                return

        except urllib2.URLError, exception:
            users.logError("/sendFile to %s failed | Reason : URL Error at /receiveFile, Exception : %s" % (destination,response))
            return

    except KeyError:

        raise cherrypy.HTTPRedirect('/')



#API for receiving files sent by other nodes
def receiveFile(data):


    #Attempt to get compulsory fields
    try:
        sender = data['sender']
        destination = data['destination']
        fileIn = data['file']
        filenameIn = data['filename']
        content_type = data['content_type']
        stamp = str(int(data['stamp']))

        #Open image for sending
        workingDir = os.path.dirname(__file__)

        #Guess extension from provided mime type
        extension = mimetypes.guess_extension(content_type)
        name = sender + stamp

        #Decode the file coming in and store it on the server
        filename = workingDir + "/serve/serverFiles/sent_files/" + name + extension
        decodedFile = base64.decodestring(fileIn)
        file = open(filename, 'wb')
        file.write(decodedFile)
        file.close()

        #Save as text message to display to screen on embedded viewer if possible
        saveMessage('/static/serverFiles/sent_files/'+ name + extension,sender,destination,stamp,'1')

        #Success code
        return '0'

    #Error code
    except KeyError:
        return '1 Missing Compulsory Field'


#Method for returning chat history between two users in html format
def getChatPage(page,sender,destination):

    #Add chat divisions to page
    workingDir = os.path.dirname(__file__)
    filename = workingDir + "/html/chatbox.html"
    f = open(filename,"r")
    page += f.read()
    f.close


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

    #For each line of dialogue, add to the chat box
    for row in rows:

        #Logic for determining which message goes on which side
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
            if (str(row[2]) == '1'):
                page +=  addEmbeddedViewer(str(row[0]))
            else: 
                page += '<div class = "chat-message">' + str(row[0]) + '</div>'
            page += '</div>'


    filename = workingDir + "/html/chatbox-bottom.html"
    f = open(filename,"r")
    page += f.read()


    return page   


#Adds an embedded viewer to the chat box, can currently show images,video and audio.
def addEmbeddedViewer(fileSource):

    if (fileSource.endswith('jpg') or fileSource.endswith('jpe') or fileSource.endswith('png') or fileSource.endswith('gif')):
        page = '<div class = "chat-message-image">'
        page += '<img src="' + fileSource + '">'
        page += '</div>'
    elif (fileSource.endswith('mp4') or fileSource.endswith('webm') or fileSource.endswith('ogg')):
        page = '<div class = "chat-message-image">'
        page += '<video width="320" controls>'
        page += '<source src="' + fileSource + '" type="video/mp4">'
        #page += '<source src="movie.ogg" type="video/ogg">'
        page += '</video>'
        page += '</div>'
    elif (fileSource.endswith('mp3') or fileSource.endswith('ogg')):
        page = '<div class = "chat-message-image">'
        page += '<audio controls>'
        page += '<source src="' + fileSource + '" type="audio/mpeg">'
        #page += '<source src="movie.ogg" type="video/ogg">'
        page += '</audio>'
        page += '</div>'
    else:
        page = 'Cannot be displayed'
    return page



#API for read receipts
def acknowledge(data):

    try:
        #Read compulsory fields
        sender = data['sender']
        stamp = data['stamp']
        hashingStandard = str(data['hashing'])
        dataHash = data['hash']


        #Grab profile picture of destination to put into chat box
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/messages.db"
        f = open(dbFilename,"r")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()
        cursor.execute("SELECT Message from Messages WHERE UPI = ? AND Stamp = ?",[sender,stamp])
        row = cursor.fetchone()

        if (hashingStandard == '0'):
            if (str(row) == dataHash):
                return '0'
            #Hash does not match
            else:
                return '7'
        elif (hashingStandard == '1'):
            hashedMessage = hashlib.sha256(str(row)).hexdigest()
            if (hashedMessage == dataHash):
                return '0'
            #Hash does not match
            else:
                return '7'
        elif (hashingStandard == '2'):
            hashedMessage = hashlib.sha256(str(row) + sender).hexdigest()
            if (hashedMessage == dataHash):
                return '0'
            #Hash does not match
            else:
                return '7'
        elif (hashingStandard == '3'):
            hashedMessage = hashlib.sha512(str(row) + sender).hexdigest()
            if (hashedMessage == dataHash):
                return '0'
            #Hash does not match
            else:
                return '7'

        #Hashing standard not supported
        else:
            return '10'

    #Missing compulsory field
    except KeyError:
        return '1'


def refreshChat():

    destination = cherrypy.session['destination']
    sender = cherrypy.session['username']

    #Grab profile picture of destination to put into chat box
    workingDir = os.path.dirname(__file__)
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

    page = ''


    #Compile the chat history between sender and destination in order
    dbFilename = workingDir + "/db/messages.db"
    f = open(dbFilename,"r")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()
    cursor.execute("SELECT Message,Sender,isFile,Stamp FROM MessageBuffer WHERE (Sender = ? AND Destination = ?) OR (Sender = ? AND Destination = ?) ORDER BY Stamp",[destination,sender,sender,destination])
    rows = cursor.fetchall()

    #For each line of dialogue, add to the chat box
    for row in rows:

        #Logic for determining which message goes on which side
        if (str(row[1]) == destination):
            page += 'd'
            page += '<div class = "user-photo"><img src = "'+picture+ '"></div>'
            if (str(row[2]) == '1'):
                page +=  addEmbeddedViewer(str(row[0]))
            else: 
                page += '<div class = "chat-message">' + str(row[0]) + '</div>'
            page += '</div>;'
            sender = 'friend'
            #acknowledgeMessage(str(row[0]),destination,str(row[2]),str(row[3]))

        else:
            page += 's'
            if (str(row[2]) == '1'):
                page +=  addEmbeddedViewer(str(row[0]))
            else: 
                page += '<div class = "chat-message">' + str(row[0]) + '</div>'
            page += '</div>;'
            sender = 'self'


    cursor.execute("DELETE FROM MessageBuffer WHERE SENDER = ? OR DESTINATION = ?",[destination,destination])
    conn.commit()
    conn.close()

    output_dict = {'newChat' : page, 'sender' : sender}
    out = json.dumps(output_dict)

    return out   


#When calling other node's acknowledge
#We will use sha-256 hashing with username as salt
def acknowledgeMessage(message,sender,stamp,isFile):


    #If the message is a file, need to open actual file before hashing
    if (isFile == '1'):

        #Open file
        workingDir = os.path.dirname(__file__)
        filename = workingDir + message
        f = open(filename)
        fileRead = f.read()

        #Hash the file
        hashData = hashlib.sha512(fileRead + sender)

    else:

        #Hash the message
        hashData = hashlib.sha512(message + sender)


    #Prepare to json encode the data
    output_dict = {'sender' : sender, 'hashing' : '3', 'hash' : hashData, 'stamp' : stamp }
    data = json.dumps(output_dict)

    #Get ip and port to construct URL
    userInfo  = users.getUserIP_PORT(destination)
    ip = userInfo['ip']
    port = userInfo['port']

    #Call sender's acknowledge
    url = "http://%s:%s/acknowledge" % (ip,port)
    req = urllib2.Request(url,data,{'Content-Type':'application/json'})

    #For now, disregard the error code returned
    response = urllib2.urlopen(req).read()

