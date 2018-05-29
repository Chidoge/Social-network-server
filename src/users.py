import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib2
import sqlite3

#Shows main page after login
@cherrypy.expose
def showUserPage():

    #Check session
    try:

        username = cherrypy.session['username']


        #Get working directory to find html and database files
        workingDir = os.path.dirname(__file__)
                
        #Serve html to page
        filename = workingDir + "/html/userpage.html"
        f = open(filename,"r")
        page = f.read()
        f.close()

        #Read database
        dbFilename = workingDir + "/db/profiles.db"
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
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + username + "&password=" + cherrypy.session['password'])
        response = r.read()

        #Split API response using white space as tokeniser
        users = response.split()

        page += '<div class = "sidebar">'
        #User list starts after 4th white space
        for i in range(5,len(users)) :

            destination = users[i].split(',')[0]
            #No need to show current user their own profile
            if (destination != username):
                page += '<p>' + destination + '</p>'
                page += '<form action ="/chatUser?destination=' + destination +'"method="post">'
                page += '<button type="submit">Chat</button></form>'

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


        #
        if (destination != ''):

            filename = workingDir + "/html/chatbox.html"
            f = open(filename,"r")
            page += f.read()
            f.close

            page += '<div id = "chatlogs" class="chatlogs">'

            dbFilename = workingDir + "/db/messages.db"
            f = open(dbFilename,"r")
            conn = sqlite3.connect(dbFilename)
            cursor = conn.cursor()

            cursor.execute("SELECT Message,Sender FROM Messages WHERE (Sender = ? AND Destination = ?) OR (Sender = ? AND Destination = ?) ORDER BY Stamp",[destination,username,username,destination])

            rows = cursor.fetchall()



            for row in rows:

                if (str(row[1]) == destination):
                    page += '<div class = "chat friend">'
                    page += '<div class = "user-photo"><img src = "'+picture+ '"></div>'
                    page += '<p class = "chat-message">' + str(row[0]) + '</p>'
                    page += '</div>'

                else:
                    page += '<div class = "chat self">'
                    #page += '<div class = "user-photo"><img src = "'+picture+ '"></div>'
                    page += '<p class = "chat-message">' + str(row[0]) + '</p>'
                    page += '</div>'

            page += '</div>'
            filename = workingDir + "/html/chatbox-bottom.html"
            f = open(filename,"r")
            page += f.read()
            f.close        

        return page 
        
    #If not logged in and trying to access userpage, bring them back to the default page
    except KeyError:

        raise cherrypy.HTTPRedirect('/')  
@cherrypy.expose
def saveOnlineUsers():

    try:
        username = cherrypy.session['username']
        #Call API to check for other online users
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + username + "&password=" + cherrypy.session['password'])
        response = r.read()
        errorCode = response[0]

        #Split API response using white space as tokeniser
        users = response.split()
            
        #Prepare database for storing online users
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/userlist.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        #User list starts after 4th white space
        for i in range(5,len(users)):

            userUPI= users[i].split(',')[0]
            userIP = users[i].split(',')[2]
            userPORT = users[i].split(',')[3]

            #Search for existing user in database
            cursor.execute("SELECT IP,PORT FROM UserList WHERE UPI = ?",[userUPI])
            row = cursor.fetchall()

            #Insert new user information if new,update existing user information
            if (len(row) == 0):
                cursor.execute("INSERT INTO UserList(UPI,IP,PORT) VALUES (?,?,?)",[userUPI,userIP,userPORT])
            else:
                cursor.execute("UPDATE UserList SET IP = ?,PORT = ? WHERE UPI = ?",[userIP,userPORT,userUPI])

        conn.commit()
        conn.close()

    except KeyError:

        return 'Session Expired'


@cherrypy.expose
def getUserIP_PORT(destination):

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

    info = {'ip' : ip, 'port' : port}

    return info


@cherrypy.expose
def setNewChatUser(destination):

    cherrypy.session['destination'] = str(destination)

    raise cherrypy.HTTPRedirect('/showUserPage')