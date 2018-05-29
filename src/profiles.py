import cherrypy
import json
import hashlib
import mimetypes
import os
import urllib
import urllib2
import sqlite3
import socket
import users

port = 15010

#Shows main page after login
@cherrypy.expose
def showUserPage():

    #Check if user is logged in before displaying
    try:
        #Do something with session username
        username = cherrypy.session['username']
        #Get working directory to find html and database file
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

        name = rows[0][0]
        position = rows[0][1]
        description = rows[0][2]
        location = rows[0][3]
        picture = rows[0][4]


        #Call API to check for other online users
        r = urllib2.urlopen("http://cs302.pythonanywhere.com/getList?username=" + username + "&password=" + cherrypy.session['password'])
        response = r.read()

        #Split API response using white space as tokeniser
        users = response.split()


        #User list starts after 4th white space
        for i in range(5,len(users)) :

            otherUser= users[i].split(',')[0]
            #No need to show current user their own profile
            if (otherUser != username):
                page += '<p>' + otherUser + '</p>'
                page += '<form action ="/viewProfile?otherUser=' + otherUser+'" method="post">'
                page += '<button type ="submit">View Profile</button></form>'
                page += '<form action ="/chat?otherUser=' + otherUser +'"method="post">'
                page += '<button type ="submit">Send Message</button></form>'



        filename = workingDir + "/html/userpage-bottom.html"
        f = open(filename,"r")
        page += f.read()
        f.close

        page = page.replace("NAME_HERE",name)
        page = page.replace('POSITION_HERE',position)
        page = page.replace('DESCRIPTION_HERE',description)
        page = page.replace('LOCATION_HERE',location)
        page = page.replace('PICTURE_HERE',picture)



        return page 
        
    #If not logged in and trying to access userpage, bring them back to the default page
    except KeyError:

        raise cherrypy.HTTPRedirect('/')   



@cherrypy.expose
def saveEdit(name=None,position=None,description=None,location=None,picture=None):
    
    #Check if user is logged in
    try:

        username = cherrypy.session['username']    
        #Get working directory to find html and database file
        workingDir = os.path.dirname(__file__)
        
        #Read database
        dbFilename = workingDir + "/db/profiles.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        cursor.execute("UPDATE Profile SET Name = ?,Position =?,Description = ?,Location = ? ,Picture = ? WHERE UPI = ?",[name,position,description,location,picture,username])
        
        #Save database changes and return user to userpage
        conn.commit()
        conn.close()
        raise cherrypy.HTTPRedirect('/showUserPage')

    except KeyError:

        raise cherrypy.HTTPRedirect('/')


#Call other node's getProfile
@cherrypy.expose
def viewProfile(otherUser):

    #Check session
    try:

        username = cherrypy.session['username']
        profile_username = otherUser

        #Open database
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/userlist.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        #Find ip and port - Should always exist, since this method is only called when this user is saved.
        cursor.execute("SELECT IP,PORT FROM UserList WHERE UPI = ?",[profile_username])
        row = cursor.fetchall()
        ip = str(row[0][0])
        port = str(row[0][1])

        #URL for requesting profile
        url = "http://"+ip+":"+port+"/getProfile"

        #Encode input arguments into json
        output_dict = {'sender' :username,'profile_username':profile_username}
        data = json.dumps(output_dict)  
        req = urllib2.Request(url,data,{'Content-Type':'application/json'})

        #Attempt to retrieve profile.
        try:

            #Load json encoded profile.
            data = urllib2.urlopen(req,timeout= 4).read()
            loaded = json.loads(data)

            #Get relevant information from the profile.
            name = loaded.get('fullname','')
            position = loaded.get('position','')
            description = loaded.get('description','')
            location = loaded.get('location','')
            picture = loaded.get('picture','')

            #Open database and store the user profile information
            workingDir = os.path.dirname(__file__)
            dbFilename = workingDir + "/db/profiles.db"
            f = open(dbFilename,"r+")
            conn = sqlite3.connect(dbFilename)
            cursor = conn.cursor()

            #Check if user profile exists in this database file
            cursor.execute("SELECT Name FROM Profile WHERE UPI = ?",[profile_username])
            row = cursor.fetchall()

            #Insert new user information if new,update existing user information
            if (len(row) == 0):
                cursor.execute("INSERT INTO Profile(Name,Position,Description,Location,Picture) VALUES (?,?,?,?)",[name,position,description,location,picture])
            else:
                cursor.execute("UPDATE Profile SET Name = ?,Position = ?,Description = ?,Location = ?,Picture = ? WHERE UPI = ?",[name,position,description,location,picture,profile_username])

            #Attempt to save the image from the given url.
            try:
                urllib.urlretrieve(picture, workingDir + "/serve/serverFiles/"+profile_username+".jpg")
            except urllib2.URLError, exception:
                pass

            conn.commit()
            conn.close()
            
            return data

        except urllib2.URLError, exception:

            return 'Sorry, we couldn\'t fetch this profile. Please try again later.'

        
        print response

    except KeyError:

        return 'Session Expired'



#Allows other users to request a profile from this node
@cherrypy.expose
def getProfile(data):

    try:

        profile_username = data['profile_username']
        sender = data['sender']

        workingDir = os.path.dirname(__file__) 


        #Get user's ip address
        hostIP = urllib2.urlopen('https://api.ipify.org').read()
        """For internal ip address"""
        #hostIP =socket.gethostbyname(socket.gethostname())


        #Construct URL for image
        url = "http://" + hostIP + ":" + str(port) + "/static/serverFiles/" + profile_username + ".jpg"

        #Open database
        dbFilename = workingDir + "/db/profiles.db"
        f = open(dbFilename,"r")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        #Read database and see if requested profile exists
        cursor.execute("SELECT Name,Position,Description,Location,Picture FROM Profile WHERE UPI = ?",[profile_username])
        row = cursor.fetchone()
        conn.close()

        if (len(row) != 0):

            output_dict = {'fullname' :row[0],'position': row[1],'description': row[2],'location': row[3],'picture': url}
            data = json.dumps(output_dict)
            return data

        else:
            return 'Requested profile does not exist'

    except KeyError:

        return '1'

    
     

    
