"""users.py

    COMPSYS302 - Software Design
    Author: Lincoln Choy

    This file contains methods which relate to the users of this server, and the login server.
"""


import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3
import communication
import time
import datetime




"""This function is used to display the html of the main page to the user
    Input : None
    Output : page (string, html code for the page)
    """
def show_user_page():

    #Check session
    try:

        username = cherrypy.session['username']

        #Get base html for page
        working_dir = os.path.dirname(__file__)
        filename = working_dir + "/html/userpage.html"
        with open (filename,'r') as file:
            page = file.read()
            file.close()

        #Check if user had chat session with anyone, if so, show their chat box
        destination = cherrypy.session.get('destination','')
        if (destination != ''):
            page = communication.get_chat_page(page,username,destination)

        page = page.replace('DESTINATION_HERE',destination)


        return page 
        
    #If not logged in and trying to access userpage, bring them back to the default page
    except KeyError:

        raise cherrypy.HTTPRedirect('/')




""" This function stores (in a database) most of the information retrieved by calling the login server's /getList API
    The information stored is useful for initiating communication with other nodes.
    Input : None
    Output : None
    """
def save_online_users():

    #Check session
    try:

        username = cherrypy.session['username']

        #Call API to check for other online users
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + username + "&password=" + cherrypy.session['password'] + "&json=1")
        response = r.read()
        errorCode = response[0]
        users = json.loads(response)

        #Prepare database for storing online users
        working_dir = os.path.dirname(__file__)
        db_filename = working_dir + "/db/userinfo.db"
        with open (db_filename,'r+'):
            conn = sqlite3.connect(db_filename)
            cursor = conn.cursor()

        for i in users:
 
            userUPI= users[i]['username']
            userIP = users[i]['ip']
            userPORT = users[i]['port']
            lastLogin = users[i]['lastLogin']

            #Search for existing user in database
            cursor.execute("SELECT IP,PORT FROM UserList WHERE UPI = '%s'" % (userUPI,))
            row = cursor.fetchall()

            #Insert new user information if new,update existing user information
            if (len(row) == 0):
                cursor.execute("INSERT INTO UserList(UPI,IP,PORT,lastLogin) VALUES ('%s','%s','%s','%s')" % (userUPI,userIP,userPORT,lastLogin,))
            else:
                cursor.execute("UPDATE UserList SET IP = '%s',PORT = '%s', lastLogin = '%s' WHERE UPI = '%s'" % (userIP,userPORT,lastLogin,userUPI,))

        conn.commit()
        conn.close()

    except KeyError:
        raise cherrypy.HTTPRedirect('/')




"""This helper function is used to get the IP and port of a user who is stored in the database.
    Input : destination (string, username of the user we are trying to get information about)
    Output : info (dictionary, contains ip and port of the destination)
    """
def get_user_ip_port(destination):

    #Open database
    working_dir = os.path.dirname(__file__)
    db_filename = working_dir + "/db/userinfo.db"
    with open (db_filename,'r+'):
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

    #Find ip and port - Should always exist, since this method is only called when this user is saved.
    cursor.execute("SELECT IP,PORT FROM UserList WHERE UPI = '%s'" % (destination,))
    row = cursor.fetchall()

    ip = str(row[0][0])
    port = str(row[0][1])

    info = {'ip' : ip, 'port' : port}

    return info




""" Helper function used to log errors into a text file
    Input : message (string, error to be logged)
    Output : None
    """
def log_error(error_message):

    working_dir = os.path.dirname(__file__)
    filename = working_dir + '/errorlog.txt'
    stamp = time.time()
    value = datetime.datetime.fromtimestamp(stamp)
    time_stamp = value.strftime('%Y-%m-%d %H:%M:%S')

    with open(filename, 'a') as file:
        file.write(error_message + '\t' + time_stamp + '\n')
        file.close()




""" Function used to set a new target destination for the chat page
    Input : destination (string, new chat target)
    Output : None
    """
def set_new_chat_user(destination):

    #Prepare database for deleting from message buffer
    working_dir = os.path.dirname(__file__)
    db_filename = working_dir + "/db/messages.db"
    with open (db_filename,'r+'):
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

    cursor.execute("DELETE FROM MessageBuffer WHERE Sender = '%s'" % (str(destination),))
    conn.commit()
    conn.close()

    cherrypy.session['destination'] = str(destination)

    raise cherrypy.HTTPRedirect('/show_user_page')




""" This function is called by a JavaScript function.
    It refreshes the online user list to be displayed on the page
    Input : None
    Output : out (json encoded dictionary, contains the html to be displayed)
    """
def refresh_user_list():

    save_online_users()

    username = cherrypy.session['username']

    #Call API to check for other online users
    response = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + username + "&password=" + cherrypy.session['password'] + "&json=1").read()
    users = json.loads(response)

    #Assemble online user list in html format.
    page = ''
    for i in users:

        destination = users[i]['username']
        #No need to show current user their own profile
        if (destination != username):
            page += '<div class = onlineUser>'
            page += '<form action ="/chat_user?destination=' +str(destination) +'"method="post">'
            page += '<button type="submit">'+'Chat with ' + str(destination) + '</button></form>'
            page += '<form action ="/view_profile?destination=' + str(destination) +  '"method="post">'
            page += '<button type="submit">' + 'View ' + str(destination) + '\'s '+ 'profile'+ '</button></form>'
            page += '</div>'


    output_dict = { "page" : page}
    out = json.dumps(output_dict)

    return out

