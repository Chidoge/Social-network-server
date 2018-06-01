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

        #Prepare database for storing message    
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/messages.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        #Store the message into database
        cursor.execute("INSERT INTO Messages(Sender,Destination,Message,Stamp,isFile) VALUES (?,?,?,?,?)",[sender,destination,message,stamp,'0'])

        #Save changes and return 0
        conn.commit()
        conn.close()

        cherrypy.session['newMessage'] = True
        return '0'

    except KeyError:

        return '1: Missing Compulsory Field'
        




#Calls the destination's /receiveMessage API to send a message to them
def sendMessage(message):


    #Check session
    try:
        sender = cherrypy.session['username']
        destination = cherrypy.session['destination']
        stamp = str(time.time())

        #Make sure user is typing in a message(cannot just be blank spaces)
        if (message == None or len(message) == 0):

            raise cherrypy.HTTPRedirect('/chatUser?destination='+destination)

        else :

            #Get IP and PORT of destination
            data = users.getUserIP_PORT(destination)
            ip = data['ip']
            port = data['port']


            #Check destination is online
            try:
                #Ping destination to see if they are online
                url = "http://%s:%s/ping?sender=%s" % (ip,port,sender)
                pingResponse = urllib2.urlopen(url,timeout=3).read()

            except urllib2.URLError, exception:
                saveErrorMessage(sender,destination,stamp)
                raise cherrypy.HTTPRedirect('/showUserPage')

            #Show error if ping response is invalid
            if (len(pingResponse) == 0 or pingResponse[0] != '0'):
                saveErrorMessage(sender,destination,stamp)
                raise cherrypy.HTTPRedirect('/showUserPage')


            #Construct the URL for calling the /receiveFile API of the destination
            url = "http://%s:%s/receiveMessage" % (ip,port)

            #Put compulsory arguments into output dictionary, then json encode it
            output_dict = {'sender' :sender,'message':message,'stamp':stamp,'destination':destination}
            data = json.dumps(output_dict)

            try:
                #Put json encoded object into http header
                req = urllib2.Request(url,data,{'Content-Type':'application/json'})
                response = urllib2.urlopen(req).read()

                if (len(response) != 0 and response[0] == '0'):
                    #Keep them on chat page
                    saveMessage(message,sender,destination,stamp,'0')
                    raise cherrypy.HTTPRedirect('/showUserPage')
                else:
                    saveError(sender,destination,stamp)
                    raise cherrypy.HTTPRedirect('/showUserPage')

            except urllib2.URLError, exception:

                saveError(sender,destination,stamp)
                raise cherrypy.HTTPRedirect('/showUserPage')


    except KeyError:

        return 'Session expired'


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
    
    #Save changes
    conn.commit()
    conn.close()



#Used to send a file which is uploaded using html file upload
def sendFile(fileData):


    #Check user session
    try:

        sender = cherrypy.session['username']
        destination = cherrypy.session['destination']

        #Add a stamp to the file and use it for the file name
        stamp = str(int(time.time()))

        #Guess an extension for the file type
        extension = mimetypes.guess_extension(str(fileData.type),strict=True)

        #Prepare file path to store on server
        workingDir = os.path.dirname(__file__)
        newfilename = workingDir + "/serve/serverFiles/sent_files/" + sender + stamp + extension

        #Write the uploaded data to a file and store it on the server
        if fileData.file: 
            with file(newfilename, 'wb') as outfile:
                outfile.write(fileData.file.read())

        #Open file and prepare to encode for sending
        image = open(newfilename, 'rb')
        imageRead = image.read()

        #Encode image in base 64
        encodedFile = base64.b64encode(imageRead)

        #Get IP and PORT of destination
        data = users.getUserIP_PORT(destination)
        ip = data['ip']
        port = data['port']


        #Check if user is online
        try:
            #Ping destination to see if they are online
            url = "http://%s:%s/ping?sender=%s" % (ip,port,sender)
            pingResponse = urllib2.urlopen(url,timeout=3).read()

        except urllib2.URLError, exception:
            saveErrorFile(sender,destination,stamp)
            raise cherrypy.HTTPRedirect('/showUserPage')

        #Show error if ping response is invalid
        if (len(pingResponse) == 0 or pingResponse[0] != '0'):
            saveErrorFile(sender,destination,stamp)
            raise cherrypy.HTTPRedirect('/showUserPage')


        #Guess the mimetype of the file to send
        content_type = mimetypes.guess_type(imageRead, strict=True)


        #Put compulsory arguments into output dictionary, then json encode it
        output_dict = {'sender' : sender,'destination' : destination,'file': encodedFile , 'filename' : sender+stamp+ extension ,'content_type' : content_type,'stamp' :stamp}
        data = json.dumps(output_dict)

        #Construct the URL for calling the /receiveFile API of the destination
        url = "http://%s:%s/receiveFile" % (ip,port)

        #Attempt to call the API, if failed, return error
        try:
            #Put json encoded object into http header
            req = urllib2.Request(url,data,{'Content-Type':'application/json'})
            response = urllib2.urlopen(req).read()

           
            #Make sure they are returning something(for interaction with substandard clients)
            if (len(response) !=0 or response[0] == '0'):

                saveMessage('/static/serverFiles/sent_files/'+sender+stamp+extension,sender,destination,stamp,'1')
                raise cherrypy.HTTPRedirect('/showUserPage')
            else:
                saveError(sender,destination,stamp)
                raise cherrypy.HTTPRedirect('/showUserPage')

        except urllib2.URLError, exception:
            saveError(sender,destination,stamp)
            raise cherrypy.HTTPRedirect('/showUserPage')
    except KeyError:
        saveError(sender,destination,stamp)
        raise cherrypy.HTTPRedirect('/showUserPage')



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

        #Decode the file coming in and store it on the server
        filename = workingDir + "/serve/serverFiles/sent_files/" + str(filenameIn)
        decodedFile = base64.decodestring(fileIn)
        file = open(filename, 'wb')
        file.write(decodedFile)

        #Save as text message to display to screen on embedded viewer if possible
        saveMessage('/static/serverFiles/sent_files/'+str(filenameIn),sender,destination,stamp,'1')

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
    return page

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

    page += '</div>'


    return page   


#Adds an embedded viewer to the chat box, can currently show images,video and audio.
def addEmbeddedViewer(fileSource):

    if (fileSource.endswith('jpg') or fileSource.endswith('jpe') or fileSource.endswith('png')):
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



#Saves the error 'Message/file not sent' and stores locally as message to display to user
def saveErrorMessage(sender,destination,stamp):

    saveMessage('Message may not have been sent properly, please try again later.',sender,destination,stamp,'0')

def saveErrorFile(sender,destination,stamp):

    saveMessage('File may not have been sent properly, please try again later.',sender,destination,stamp,'0')


#API for read receipts
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


    output_dict = {'page' : page , 'newMessaage' : str(cherrypy.session.get('newMessage',''))}
    cherrypy.session['newMessage'] = False
    out = json.dumps(output_dict)

    return out   