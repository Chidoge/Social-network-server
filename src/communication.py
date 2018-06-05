"""communication.py

    COMPSYS302 - Software Design
    Author: Lincoln Choy

This file contains all the functions and API's which help with node to node communication
    Currently there is no encryption supported.
"""

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


"""This function/API is called when other nodes want to send this client a message, and this function
    will store the message in a database and return a '0' if successful.
    Inputs : data (dictionary, contains information about the sender,destination and the message)
    Outputs : errorcode (string, currently this only returns '0','1',9', or '11', read the application protocol for the meanings of the error codes)
    """
def receive_message(data):

    #Attempt to get the compulsory fields
    try:

        sender = data['sender']
        destination =  data['destination']
        message = data['message']
        stamp = data['stamp']

        is_rate_limited = check_rate_limit(sender)
        if (is_rate_limited == '1'):
            users.log_error('Rate Limited User : %s' % sender)
            return '11'

        #Check if message is encrypted
        encryption = data.get('encryption','0')

        #Does not support encryption
        if (encryption != '0'):
            return '9'

        #Prepare database for storing message    
        working_dir = os.path.dirname(__file__)
        db_filename = working_dir + "/db/messages.db"
        with open (db_filename,'r+'):
            conn = sqlite3.connect(db_filename)
            cursor = conn.cursor()

        #Store the message into database
        cursor.execute("INSERT INTO Messages(Sender,Destination,Message,Stamp,isFile) VALUES ('%s','%s','%s','%s','%s')" % (sender,destination,message,stamp,'0',))
        cursor.execute("INSERT INTO MessageBuffer(Sender,Destination,Message,Stamp,isFile) VALUES ('%s','%s','%s','%s','%s')" % (sender,destination,message,stamp,'0',))

        #Save changes and return 0
        conn.commit()
        conn.close()


        return '0'

    #Missing compulsory field
    except KeyError:
        return '1'





"""This function allows this client to send a message to another node, the destination of the message
    is stored in the cherrypy session object with the key 'destination'. The message is also stored
    in a database so that this sender may display it in the chat history.
    Inputs : message (string)
    Output : None
    """
def send_message(message):

    #Check session
    try:

        sender = cherrypy.session['username']
        destination = cherrypy.session['destination']


        #Get IP and PORT of destination
        data = users.get_user_ip_port(destination)
        ip = data['ip']
        port = data['port']


        #Check destination is online
        try:
            #Ping destination to see if they are online
            url = "http://%s:%s/ping?sender=%s" % (ip,port,sender)
            ping_response = urllib2.urlopen(url,timeout=2).read()

            #Show error if ping response is invalid
            if (len(ping_response) == 0 or ping_response[0] != '0'):
                users.log_error("/send_message to %s failed | Reason : Ping response was not 0, Response : %s" % (destination,ping_response))
                return

        except urllib2.URLError,exception:
            users.log_error("/send_message to %s failed | Reason : URL Error at /ping, Exception : %s" % (destination,exception))
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
                save_message(message,sender,destination,stamp,'0')
                return
            else:
                users.log_error("/send_message to %s failed | Reason : /receiveMessage response was not 0, Response : %s" % (destination,response))
                return

        except urllib2.URLError,exception:
            users.logError("/send_message to %s failed | Reason : URL Error at /receiveMessage, Exception : %s" % (destination,exception))
            return


    except KeyError:

        raise cherrypy.HTTPRedirect('/')





"""This helper function stores each message, whether it be sent or received, in
    a message table and a buffer table (in the same database file) which loads the message directly into the chat box via JavaScript
    Inputs : message (string)
             sender (string)
             destination (string)
             stamp (string)
             is_file (string)
    Output : None
    """
def save_message(message,sender,destination,stamp,is_file):

    #Prepare database for message storing
    working_dir = os.path.dirname(__file__)
    db_filename = working_dir + "/db/messages.db"
    with open (db_filename,'r+'):
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

    #Insert message row
    cursor.execute("INSERT INTO Messages(Sender,Destination,Message,Stamp,isFile) VALUES ('%s','%s','%s','%s','%s')" % (sender,destination,message,stamp,is_file,))
    cursor.execute("INSERT INTO MessageBuffer(Sender,Destination,Message,Stamp,isFile) VALUES ('%s','%s','%s','%s','%s')" % (sender,destination,message,stamp,is_file,))

    #Save changes
    conn.commit()
    conn.close()





"""This function/API is usually called before another client initiates communication with this node
    It is useful to check the sender of the ping for rate limiting purposes.
    Input : sender (string)
    Output : error_code (string, '0' or '11', check application protocol for meanings of the error codes)
    """
def ping(sender):

    is_rate_limited = check_rate_limit(sender)

    if (is_rate_limited == '1'):
        users.log_error('Rate Limited User : %s' % sender)
        return '11'
    else :
        return '0'





"""This function is used to send a file via calling the other node's /receiveFile API,
    the filepath of the file is stored in the database,while the file is stored somewhere else in
    the server directory.
    Inputs : file_data (string, the file_data encoded in a base 64 string)
             mime_type (string, mime_type of the file,used to guess the extension)
    Output : None
    """
def send_file(file_data,mime_type):


    #Check user session
    try:

        sender = cherrypy.session['username']
        destination = cherrypy.session['destination']

        #Add a stamp to the file and use it for the file name
        stamp = str(int(time.time()))

        #Guess an extension for the file type
        extension = mimetypes.guess_extension(str(mime_type),strict=True)

        #Prepare file path to store on server
        working_dir = os.path.dirname(__file__)
        new_filename = working_dir + "/serve/serverFiles/sent_files/" + sender + stamp + extension

        #Store the file locally
        decoded_file = base64.decodestring(file_data)
        with open (new_filename,'wb') as file :
            file.write(decoded_file)
            file.close()
 

        #file_data is passed in as base 64
        encoded_file = file_data

        #Get IP and PORT of destination
        data = users.get_user_ip_port(destination)
        ip = data['ip']
        port = data['port']

        #Check if user is online
        try:
            #Ping destination to see if they are online
            url = "http://%s:%s/ping?sender=%s" % (ip,port,sender)
            ping_response = urllib2.urlopen(url,timeout=2).read()

            #Show error just in case destination didn't implement ping properly
            if (len(ping_response) == 0 or ping_response[0] != '0'):
                users.log_error("/send_file to %s failed | Reason : Ping response was not 0, Response : %s" % (destination,ping_response))
                return

        except urllib2.URLError,exception:
            users.log_error("/send_file to %s failed | Reason : URL Error at /ping, Exception : %s" % (destination,exception))
            return


        #Put compulsory arguments into output dictionary, then json encode it
        output_dict = {'sender' : sender,'destination' : destination,'file': encoded_file , 'filename' : sender + stamp + extension ,'content_type' : mime_type,'stamp' :stamp}
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

                save_message('/static/serverFiles/sent_files/'+sender+stamp+extension,sender,destination,stamp,'1')
                return
            else:
                users.log_error("/send_file to %s failed | Reason : /receiveFile response was not 0, Response : %s" % (destination,response))
                return

        except urllib2.URLError,exception:
            users.log_error("/send_file to %s failed | Reason : URL Error at /receiveFile, Exception : %s" % (destination,exception))
            return

    except KeyError:

        raise cherrypy.HTTPRedirect('/')





"""This function/API is called when another client wants to send this node a file.
    The file is stored somewhere on the server and the filepath is stored a database.
    This filepath is stored as a message so that the embedded viewer knows where to look
    when displaying this file in the chat history.
    Input : data (dictionary, contains information about the sender and the file)
    Output : error_code ('0' or '1')
    """
def receive_file(data):


    #Attempt to get compulsory fields
    try:
        sender = data['sender']
        destination = data['destination']
        fileIn = data['file']
        filenameIn = data['filename']
        content_type = data['content_type']
        stamp = str(int(float(str(data['stamp']))))

        #Currently do not support any standard of encryption
        encryption = data.get('encryption','0')
        if (encryption != '0'):
            return '9'


        #Get working directory
        working_dir = os.path.dirname(__file__)

        #Get extension from filename
        index = filenameIn.rfind('.')
        if (index != -1):
            extension = filenameIn[index:]
        else:
            extension = mimetypes.guess_extension(content_type)

        name = sender + stamp

        #Decode the file coming in and store it on the server
        filename = working_dir + "/serve/serverFiles/sent_files/" + name + extension
        decoded_file = base64.decodestring(fileIn)
        with open (filename,'wb') as file:
            file.write(decoded_file)
            file.close()


        #Save as text message to display to screen on embedded viewer if possible
        save_message('/static/serverFiles/sent_files/'+ name + extension,sender,destination,stamp,'1')

        #Success code
        return '0'

    #Error code
    except KeyError:
        return '1 Missing Compulsory Field'





"""This function is used to check the requests of a certain user in the past minute.
    Users are limited to 60 requests per minute to prevent traffic congestion of the server
    Input : sender (string)
    Output : error_code ('0' or '1', '0' indicates not rate limited, '1' indicates otherwise)
    """
def check_rate_limit(sender):

    #Open database and check for requests limit
    working_dir = os.path.dirname(__file__)
    db_filename = working_dir + "/db/userinfo.db"
    f = open(db_filename,'r')
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()


    cursor.execute("SELECT lastLimit,requestsPastMinute FROM UserList WHERE UPI = '%s'" % (sender,))
    row = cursor.fetchall()

    if (len(row)==0):
        #Do not trust anyone not on userlist
        #Return rate limited error code
        return '1'
    else:
        if (time.time()- float(str(row[0][0])) > 60):
            cursor.execute("UPDATE UserList SET lastLimit = '%s',requestsPastMinute = '%s' WHERE UPI = '%s'" % (str(time.time()),'1',sender,))
            conn.commit()
            conn.close()
            return '0'
        else:
            #Row 1 is the requests in the past minute
            if (int(str(row[0][1])) < 60):
                cursor.execute("UPDATE UserList SET requestsPastMinute = '%s' WHERE UPI = '%s'" % (str(int(str(row[0][1])) + 1),sender,))
                conn.commit()
                conn.close()
                return '0'
            else:
                return '1'





"""This function returns a string of html code which displays the chat history on the browser
    Inputs : page (string)
             sender (string)
             destination (string)
    Output : page (string, html to be displayed in the browser, is concatenated with the input argument : 'page')
    """
def get_chat_page(page,sender,destination):

    #Add chat divisions to page
    working_dir = os.path.dirname(__file__)
    filename = working_dir + "/html/chatbox.html"
    with open (filename,'r') as file:
        page += file.read()
        file.close()

    #Grab profile picture of destination to put into chat box
    db_filename = working_dir + "/db/userinfo.db"

    with open (db_filename,'r'):
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

    cursor.execute("SELECT Picture FROM Profile WHERE UPI = '%s'" % (destination,))
    row = cursor.fetchone()

    #Use anon picture if they dont have a picture
    if (row == None):

        picture = '/static/css/anon.png'

    elif (str(row[0]) == 'None'):

        picture = '/static/css/anon.png'
    else:

        picture = str(row[0])


    #Compile the chat history between sender and destination in order
    db_filename = working_dir + "/db/messages.db"
    with open (db_filename,'r'):
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

    cursor.execute("SELECT Message,Sender,isFile FROM Messages WHERE (Sender = '%s' AND Destination = '%s') OR (Sender = '%s' AND Destination = '%s') ORDER BY Stamp" % (destination,sender,sender,destination,))
    rows = cursor.fetchall()

    #For each line of dialogue, add to the chat box
    for row in rows:

        #Logic for determining which message goes on which side
        if (str(row[1]) == destination):
            page += '<div class = "chat friend">'
            page += '<div class = "user-photo"><img src = "' + picture + '"></div>'
            if (str(row[2]) == '1'):
                page +=  add_embedded_viewer(str(row[0]))
            else: 
                page += '<div class = "chat-message">' + str(row[0]) + '</div>'
            page += '</div>'

        else:
            page += '<div class = "chat self">'
            if (str(row[2]) == '1'):
                page +=  add_embedded_viewer(str(row[0]))
            else: 
                page += '<div class = "chat-message">' + str(row[0]) + '</div>'
            page += '</div>'


    filename = working_dir + "/html/chatbox-bottom.html"
    with open (filename,'r') as file:
        page += file.read()
        file.close()

    return page





"""This helper function adds an embedded viewer to the html page for displaying images,videos,songs, and pdf's
    Input : file_source (string, relative path of the file to be displayed)
    Output : page (string, html code)
    """
def add_embedded_viewer(file_source):

    if (file_source.endswith('jpg') or file_source.endswith('jpe') or file_source.endswith('png') or file_source.endswith('gif')):
        page = '<div class = "chat-message-image">'
        page += '<img src="' + file_source + '">'
        page += '</div>'
    elif (file_source.endswith('mp4') or file_source.endswith('webm') or file_source.endswith('ogg')):
        page = '<div class = "chat-message-image">'
        page += '<video width="320" controls>'
        page += '<source src="' + file_source + '" type="video/mp4">'
        page += '</video>'
        page += '</div>'
    elif (file_source.endswith('mp3') or file_source.endswith('ogg')):
        page = '<div class = "chat-message-image">'
        page += '<audio controls>'
        page += '<source src="' + file_source + '" type="audio/mpeg">'
        page += '</audio>'
        page += '</div>'
    elif (file_source.endswith('pdf')):
        #page = '<div class = "chat-message">'
        page = '<div class = "chat-message-PDF">'
        page += '<object data="' + file_source + '" type="application/pdf" width="350px" height="450px"></object></div>'
    else:
        page = '<div class = "chat-message">File format is not supported</div>'
    return page



"""API for acknowledge, used to implement read receipts
    NOT TESTED FOR WORKING
    """
def acknowledge(data):

    try:
        #Read compulsory fields
        sender = data['sender']
        stamp = data['stamp']
        hashing_standard = str(data['hashing'])
        data_hash = data['hash']


        #Grab profile picture of destination to put into chat box
        working_dir = os.path.dirname(__file__)
        db_filename = working_dir + "/db/messages.db"
        f = open(db_filename,"r")
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.execute("SELECT Message from Messages WHERE UPI = '%s' AND Stamp = '%s'" % (sender,stamp,))
        row = cursor.fetchone()

        if (hashing_standard == '0'):
            if (str(row) == data_hash):
                return '0'
            #Hash does not match
            else:
                return '7'
        elif (hashing_standard == '1'):
            hashed_message = hashlib.sha256(str(row)).hexdigest()
            if (hashed_message == data_hash):
                return '0'
            #Hash does not match
            else:
                return '7'
        elif (hashing_standard == '2'):
            hashed_message = hashlib.sha256(str(row) + sender).hexdigest()
            if (hashed_message == data_hash):
                return '0'
            #Hash does not match
            else:
                return '7'
        elif (hashing_standard == '3'):
            hashed_message = hashlib.sha512(str(row) + sender).hexdigest()
            if (hashed_message == data_hash):
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





"""This function is called by a JavaScript function, and is used to check for buffered messages yet to be displayed on the browser
    Input : None
    Output : out (json encoded dictionary, contains information about new messages received)
    """
def refresh_chat():

    destination = cherrypy.session['destination']
    sender = cherrypy.session['username']

    #Grab profile picture of destination to put into chat box
    working_dir = os.path.dirname(__file__)
    db_filename = working_dir + "/db/userinfo.db"
    with open (db_filename,'r'):
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()  

    cursor.execute("SELECT Picture FROM Profile WHERE UPI = '%s'" % (destination,))
    row = cursor.fetchone()

    #Use anon picture if they dont have a picture
    if (row == None):

        picture = '/static/css/anon.png'

    elif (str(row[0]) == 'None'):

        picture = '/static/css/anon.png'
    else:
        picture = str(row[0])

    page = ''


    #Get new messages from destination or sender
    db_filename = working_dir + "/db/messages.db"
    with open (db_filename,'r'):
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

    cursor.execute("SELECT Message,Sender,isFile,Stamp FROM MessageBuffer WHERE (Sender = '%s' AND Destination = '%s') OR (Sender = '%s' AND Destination = '%s') ORDER BY Stamp" % (destination,sender,sender,destination,))
    rows = cursor.fetchall()

    #For each line of dialogue, add to the chat box
    for row in rows:

        #Logic for determining which message goes on which side
        if (str(row[1]) == destination):
            page += 'd'
            page += '<div class = "user-photo"><img src = "' + picture + '"></div>'
            if (str(row[2]) == '1'):
                page +=  add_embedded_viewer(str(row[0]))
            else: 
                page += '<div class = "chat-message">' + str(row[0]) + '</div>'
            page += '</div>;'
            sender = 'friend'
            #acknowledge_message(str(row[0]),destination,str(row[2]),str(row[3]))

        else:
            page += 's'
            if (str(row[2]) == '1'):
                page +=  add_embedded_viewer(str(row[0]))
            else: 
                page += '<div class = "chat-message">' + str(row[0]) + '</div>'
            page += '</div>;'
            sender = 'self'


    cursor.execute("DELETE FROM MessageBuffer WHERE SENDER = '%s' OR DESTINATION = '%s'" % (destination,destination,))
    conn.commit()
    conn.close()

    output_dict = {'newChat' : page, 'sender' : sender}
    out = json.dumps(output_dict)

    return out   





"""This function is used to acknowledge a message received, so other nodes can display read receipts.
    NOT TESTED FOR WORKING
    """
def acknowledge_message(message,sender,stamp,is_file):


    #If the message is a file, need to open actual file before hashing
    if (is_file == '1'):

        #Open file
        working_dir = os.path.dirname(__file__)
        filename = working_dir + message
        with open(filename,'r') as file:
            file_read = file.read()

        #Hash the file
        hash_data = hashlib.sha512(file_read + sender)

    else:

        #Hash the message
        hash_data = hashlib.sha512(message + sender)


    #Prepare to json encode the data
    output_dict = {'sender' : sender, 'hashing' : '3', 'hash' : hash_data, 'stamp' : stamp }
    data = json.dumps(output_dict)

    #Get ip and port to construct URL
    user_info  = users.get_user_ip_port(destination)
    ip = user_info['ip']
    port = user_info['port']

    #Call sender's acknowledge
    url = "http://%s:%s/acknowledge" % (ip,port)
    req = urllib2.Request(url,data,{'Content-Type':'application/json'})

    #For now, disregard the error code returned
    response = urllib2.urlopen(req).read()





"""This function adds notifications for new messages at the top of the page.
    It does this by checking the buffered messages table.
    Input : None
    Output : out (json encoded dictionary, contains information about the sender)
    """
def notify():

    sender = cherrypy.session['username']

    #See if new messages exist 
    working_dir = os.path.dirname(__file__)
    db_filename = working_dir + "/db/messages.db"
    with open (db_filename,'r'):
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

    cursor.execute("SELECT * FROM MessageBuffer WHERE Destination = '%s'" % (sender,))
    rows = cursor.fetchall()

    #Check message buffer for unread messages and get their senders
    #Display these senders' names on the page using JavaScript
    destination = []
    if (len(rows) != 0):
        for row in rows:
            destination.append(str(row[0]))

        destination = set(destination)
        messageFrom = ''
        for element in destination:
            messageFrom += element + ' '

        output_dict = {'newMessage': 'True', 'destination' : messageFrom}
        out = json.dumps(output_dict)
        return out
    else:

        output_dict = {'newMessage': 'False'}
        out = json.dumps(output_dict)
        return out