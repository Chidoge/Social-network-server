import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3
import communication


#Shows main page after login
def showUserPage():

    #Check session
    try:

        username = cherrypy.session['username']

        #Get base html for page
        workingDir = os.path.dirname(__file__)
        filename = workingDir + "/html/userpage.html"
        f = open(filename,"r")
        page = f.read()
        f.close()

        #Call API to check for other online users
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + username + "&password=" + cherrypy.session['password'] + "&json=1")
        response = r.read()
        users = json.loads(response)

        #Assemble online user list in html format.
        page += '<div class = "sidebar">'
        for i in users:
 
            destination= users[i]['username']
            #No need to show current user their own profile
            if (destination != username):
                page += '<div class = onlineUser>'
                page += '<p>' + destination + '</p>' 
                page += '<form action ="/chatUser?destination=' + destination +'"method="post">'
                page += '<button type="submit">Chat</button></form>'
                page += '<form action ="/viewProfile?destination=' + destination + '"method="post">'
                page += '<button type="submit">View Profile</button></form>'
                page += '</div>'

        page += '</div></div>'

        #Check if user had chat session with anyone, if so, show their chat box
        destination = cherrypy.session.get('destination','')
        if (destination != ''):
            page = communication.getChatPage(page,username,destination)

        page = page.replace('DESTINATION_HERE',destination)

        return page 
        
    #If not logged in and trying to access userpage, bring them back to the default page
    except KeyError:

        raise cherrypy.HTTPRedirect('/')  



def saveOnlineUsers():

    #Check session
    try:

        username = cherrypy.session['username']

        #Call API to check for other online users
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + username + "&password=" + cherrypy.session['password'] + "&json=1")
        response = r.read()
        errorCode = response[0]
        users = json.loads(response)

        #Prepare database for storing online users
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/userinfo.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        for i in users:
 
            userUPI= users[i]['username']
            userIP = users[i]['ip']
            userPORT = users[i]['port']
            lastLogin = users[i]['lastLogin']

            #Search for existing user in database
            cursor.execute("SELECT IP,PORT FROM UserList WHERE UPI = ?",[userUPI])
            row = cursor.fetchall()

            #Insert new user information if new,update existing user information
            if (len(row) == 0):
                cursor.execute("INSERT INTO UserList(UPI,IP,PORT,lastLogin) VALUES (?,?,?,?)",[userUPI,userIP,userPORT,lastLogin])
            else:
                cursor.execute("UPDATE UserList SET IP = ?,PORT = ?, lastLogin = ? WHERE UPI = ?",[userIP,userPORT,lastLogin,userUPI])

        conn.commit()
        conn.close()

    except KeyError:

        raise cherrypy.HTTPRedirect('/')



def getUserIP_PORT(destination):

    #Open database
    workingDir = os.path.dirname(__file__)
    dbFilename = workingDir + "/db/userinfo.db"
    f = open(dbFilename,"r+")
    conn = sqlite3.connect(dbFilename)
    cursor = conn.cursor()


    #Find ip and port - Should always exist, since this method is only called when this user is saved.
    cursor.execute("SELECT IP,PORT FROM UserList WHERE UPI = ?",[destination])
    row = cursor.fetchall()

    ip = str(row[0][0])
    port = str(row[0][1])

    info = {'ip' : ip, 'port' : port}

    return info



def setNewChatUser(destination):

    cherrypy.session['destination'] = str(destination)

    raise cherrypy.HTTPRedirect('/showUserPage')

@cherrypy.expose
def refreshUserList():

    username = cherrypy.session['username']

    #Get base html for page
    workingDir = os.path.dirname(__file__)
    filename = workingDir + "/html/userpage.html"
    f = open(filename,"r")
    #page = f.read()
    f.close()

    #Call API to check for other online users
    r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + username + "&password=" + cherrypy.session['password'] + "&json=1")
    response = r.read()
    users = json.loads(response)

    #Assemble online user list in html format.
    page = '<div class = "sidebar">'
    for i in users:

        destination= users[i]['username']
        #No need to show current user their own profile
        if (destination != username):
            page += '<div class = onlineUser>'
            page += '<p>' +  str(destination) + '</p>' 
            page += '<form action ="/chatUser?destination=' + str(destination) +'"method="post">'
            page += '<button type="submit">Chat</button></form>'
            page += '<form action ="/viewProfile?destination=' +  str(destination) + '"method="post">'
            page += '<button type="submit">View Profile</button></form>'
            page += '</div>'

    page += '</div></div>'

    output_dict = { "page" : page}
    out = json.dumps(output_dict)

    return out
