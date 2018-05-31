import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3
import communication

#Shows main page after login
@cherrypy.expose
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

        #Read database
        dbFilename = workingDir + "/db/userinfo.db"
        f = open(dbFilename,"r")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()
        cursor.execute("SELECT Name, Position, Description,Location,Picture FROM Profile where UPI = ?",[username])

        rows = cursor.fetchall()

        name = str(rows[0][0])
        position = str(rows[0][1])
        description = str(rows[0][2])
        location = str(rows[0][3])
        picture = str(rows[0][4])


        #Call API to check for other online users
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + username + "&password=" + cherrypy.session['password'] + "&json=1")
        response = r.read()
        users = json.loads(response)


        page += '<div class = "sidebar">'
        for i in users:
 
            destination= users[i]['username']
            #No need to show current user their own profile
            if (destination != username):
                page += '<div class = onlineUser>'
                page += '<p>' + destination + '</p>' 
                #page += '<div style ="float:left">'
                page += '<form action ="/chatUser?destination=' + destination +'"method="post">'
                page += '<button type="submit">Chat</button></form>'
                #page += '</div>'
                #page += '<div style ="float:right">'
                page += '<form action ="/viewProfile?destination=' + destination + '"method="post">'
                page += '<button type="submit">View Profile</button></form>'
                #page += '</div>'
                page += '</div>'

        page += '</div>'

        page = page.replace('NAME_HERE',name)
        page = page.replace('POSITION_HERE',position)
        page = page.replace('DESCRIPTION_HERE',description)
        page = page.replace('LOCATION_HERE',location)
        page = page.replace('PICTURE_HERE',picture)

        page = page.replace('NAME_FORM',"'"+name+"'")
        page = page.replace('POSITION_FORM',"'"+position+"'")
        page = page.replace('DESCRIPTION_FORM',"'"+description+"'")
        page = page.replace('LOCATION_FORM',"'"+location+"'")

        destination = cherrypy.session.get('destination','')


        if (destination != ''):
            page = communication.getChatPage(page,username,destination)

        page = page.replace('DESTINATION_HERE',destination)
        return page 
        
    #If not logged in and trying to access userpage, bring them back to the default page
    except KeyError:

        raise cherrypy.HTTPRedirect('/')  



@cherrypy.expose
def saveOnlineUsers():

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

        return 'Session Expired'



@cherrypy.expose
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


@cherrypy.expose
def setNewChatUser(destination):

    cherrypy.session['destination'] = str(destination)

    raise cherrypy.HTTPRedirect('/showUserPage')