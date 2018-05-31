import cherrypy
import json
import mimetypes
import os
import urllib
import urllib2
import sqlite3
import users
import time

port = 15010


#Call other node's getProfile
@cherrypy.expose
def viewProfile(destination):

    #Check session
    try:

        username = cherrypy.session['username']
        profile_username = destination

        #Open database
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/userinfo.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        #Find ip and port - Should always exist, since this method is only called when this user is saved.
        cursor.execute("SELECT IP,PORT FROM UserList WHERE UPI = ?",[profile_username])
        row = cursor.fetchall()
        ip = str(row[0][0])
        port = str(row[0][1])

        #Construct URL for requesting profile
        url = "http://"+ip+":"+port+"/getProfile"

        #Encode input arguments into json
        output_dict = {'sender' :username,'profile_username':profile_username}
        data = json.dumps(output_dict)

        #Put arguments into url header  
        req = urllib2.Request(url,data,{'Content-Type':'application/json'})

        #Attempt to retrieve profile.
        try:

            #Load json encoded profile. Give 4 second for other side to respond.
            data = urllib2.urlopen(req,timeout= 4).read()

            #Make sure object being returned is a json object
            try:

                loaded = json.loads(data)
                #Get relevant information from the profile.
                name = loaded.get('fullname','')
                position = loaded.get('position','')
                description = loaded.get('description','')
                location = loaded.get('location','')
                lastUpdated = loaded.get('lastUpdated','0')
                picture = str(loaded.get('picture','None'))

                #Open database and store the user profile information
                workingDir = os.path.dirname(__file__)
                dbFilename = workingDir + "/db/userinfo.db"
                f = open(dbFilename,"r+")
                conn = sqlite3.connect(dbFilename)
                cursor = conn.cursor()

                #Check if user profile exists in this database file
                cursor.execute("SELECT Name FROM Profile WHERE UPI = ?",[profile_username])
                row = cursor.fetchall()

                userInfo = users.getUserIP_PORT(profile_username)
                ip = userInfo['ip']
                port = userInfo['port']

                if ('http' not in picture and '/' in picture):
                    picture = 'http://'+ip+":"+port+picture

                elif('http' in picture):
                    pass
                else:
                    picture = 'None'

                #Insert new user information if new, otherwise update existing profile.
                #TODO: ADD lastUpdated implementation
                if (len(row) == 0):
                    cursor.execute("INSERT INTO Profile(UPI,Name,Position,Description,Location,Picture,lastUpdated) VALUES (?,?,?,?,?,?,?)",[profile_username,name,position,description,location,picture,lastUpdated])
                else:
                    cursor.execute("UPDATE Profile SET UPI = ?,Name = ?,Position = ?,Description = ?,Location = ?,Picture = ?, lastUpdated = ? WHERE UPI = ?",[profile_username,name,position,description,location,picture,lastUpdated,profile_username])


                if ('http' in picture):
                    #Attempt to save the profile image from the given url.
                    try:
                        urllib.urlretrieve(picture, workingDir + "/serve/serverFiles/profile_pictures/"+profile_username+".jpg")
                        cursor.execute("UPDATE Profile SET Picture = ? WHERE UPI = ?",["/static/serverFiles/profile_pictures/"+profile_username+".jpg",profile_username])
                    except urllib2.URLError, exception:
                        cursor.execute("UPDATE Profile SET Picture = ? WHERE UPI = ?",['None',profile_username])

                #Save database changes
                conn.commit()
                conn.close()

                return data

            except ValueError:

                return 'Sorry, we couldn\'t fetch this profile. Please try again later.'

            


        #In case API call fails.
        except urllib2.URLError, exception:

            return 'Sorry, we couldn\'t fetch this profile. Please try again later.'


    except KeyError:

        return 'Session Expired'



#Allows other users to request a profile from this node
@cherrypy.expose
def getProfile(data):

    #Try block; in case the API caller didn't add the compulsory input arguments
    try:

        #Extract inputs for this API call
        profile_username = data['profile_username']
        sender = data['sender']

        #Get user's ip address
        hostIP = urllib2.urlopen('https://api.ipify.org').read()
        """For internal ip address"""
        #hostIP =socket.gethostbyname(socket.gethostname())

        #Open database for extracting profile
        workingDir = os.path.dirname(__file__) 
        dbFilename = workingDir + "/db/userinfo.db"
        f = open(dbFilename,"r")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()




        #Read database and see if requested profile exists
        cursor.execute("SELECT Name,Position,Description,Location,Picture,lastUpdated FROM Profile WHERE UPI = ?",[profile_username])
        row = cursor.fetchone()

        #Construct URL for image
        url = "http://" + hostIP + ":" + str(port) + "/" + row[4]

        conn.close()

        #Check if profile exists in the database
        if (len(row) != 0):

            #Extract profile information in the rows and store it into a dictonary object to json encode later
            output_dict = {'fullname' :row[0],'position': row[1],'description': row[2],'location': row[3],'picture': url,'lastUpdated':row[5]}

            #Json encode the output dictionary then return it
            data = json.dumps(output_dict)
            return data

        else:

            return 'Requested profile does not exist'


    #Return error code 1 : Missing compulsory field
    except KeyError:

        return '1'


@cherrypy.expose
def viewOwnProfile():

    #Check session
    try:

        username = cherrypy.session['username']

        #Read database
        workingDir = os.path.dirname(__file__)
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


        #Prepare html
        workingDir = os.path.dirname(__file__)
        filename = workingDir + "/html/ownProfile.html"
        f = open(filename,"r")
        page = f.read()


        page = page.replace('NAME_HERE',name)
        page = page.replace('POSITION_HERE',position)
        page = page.replace('DESCRIPTION_HERE',description)
        page = page.replace('LOCATION_HERE',location)
        page = page.replace('PICTURE_HERE',picture)

        page = page.replace('NAME_FORM',"'"+name+"'")
        page = page.replace('POSITION_FORM',"'"+position+"'")
        page = page.replace('DESCRIPTION_FORM',"'"+description+"'")
        page = page.replace('LOCATION_FORM',"'"+location+"'")
        return page

    except KeyError:
        raise cherrypy.HTTPRedirect('/')


#Function that saves user's profile edits
@cherrypy.expose
def saveEdit(name,position,description,location):
    
    #Check user session
    try:

        username = cherrypy.session['username']  

        #Prepare database for writing to
        workingDir = os.path.dirname(__file__)
        dbFilename = workingDir + "/db/userinfo.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        #Key for last updated profile
        lastUpdated = time.time()

        cursor.execute("UPDATE Profile SET Name = ?,Position =?,Description = ?,Location = ? ,lastUpdated = ? WHERE UPI = ?",[name,position,description,location,lastUpdated,username])

        #Save database changes and return to userpage
        conn.commit()
        conn.close()

        raise cherrypy.HTTPRedirect('/showUserPage')

    #Redirect to index
    except KeyError:

        raise cherrypy.HTTPRedirect('/')


#Updates user's profile picture
@cherrypy.expose
def editPicture(picture):

    #Check session
    try:
        username = cherrypy.session['username']

        #Guess an extension for the file type
        fileType = mimetypes.guess_type(str(picture))

        #Prepare file path to store on server
        workingDir = os.path.dirname(__file__)
        newfilename = workingDir + "/serve/serverFiles/profile_pictures/" + username + ".jpg"

        #Write the uploaded data to a file and store it on the server
        if picture.file: 
            with file(newfilename, 'wb') as outfile:
                outfile.write(picture.file.read())

        #Prepare database for writing to
        dbFilename = workingDir + "/db/userinfo.db"
        f = open(dbFilename,"r+")
        conn = sqlite3.connect(dbFilename)
        cursor = conn.cursor()

        picture = "/static/serverFiles/profile_pictures/" + username + ".jpg"

        cursor.execute("UPDATE Profile SET Picture = ? WHERE UPI = ?",[picture,username])

        #Save database changes and return to userpage
        conn.commit()
        conn.close()

        raise cherrypy.HTTPRedirect('/viewOwnProfile')

    except KeyError:
        raise cherrypy.HTTPRedirect('/')
