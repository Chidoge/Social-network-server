"""profiles.py

    COMPSYS302 - Software Design
    Author: Lincoln Choy
    
This file contains functions and API's which help with the retrieval,editing and
display of profiles for the server.
"""

import cherrypy
import json
import mimetypes
import os
import urllib
import urllib2
import sqlite3
import users
import time
import socket

port = 10010

#Get user's ip address
#host_IP = urllib2.urlopen('https://api.ipify.org').read()
"""For internal ip address"""
host_IP = socket.gethostbyname(socket.gethostname())


""" This function returns a string of html which is the page that displays information
    for a requested profile.
    Input : destination (string, the name of the person's profile to be displayed)
    Output : page (string, a string of html code to be displayed on the browser)
    """
def view_profile(destination):

    #Check session
    try:

        username = cherrypy.session['username']
        profile_username = destination

        user_info = users.get_user_ip_port(profile_username)
        ip = user_info['ip']
        port = user_info['port']


        #Check destination is online
        try:
            #Ping destination to see if they are online
            url = "http://%s:%s/ping?sender=%s" % (ip,port,username)
            ping_response = urllib2.urlopen(url,timeout=2).read()

        except urllib2.URLError, exception:
            users.log_error("/viewProfile for %s failed | Reason : URL Error at /ping, Exception : %s" % (profile_username,exception))
            return 'Sorry, we couldn\'t fetch this profile. Please try again later.'

        #Show error if ping response is invalid
        if (len(ping_response) == 0 or ping_response[0] != '0'):
            users.log_error("/viewProfile for %s failed | Reason : Ping response was not 0, Response : %s" % (profile_username,ping_response))
            return 'Sorry, we couldn\'t fetch this profile. Please try again later.'

        #Construct URL for requesting profile
        url = ("http://%s:%s/getProfile" %(ip,port))

        #Encode input arguments into json
        output_dict = {'sender' :username,'profile_username':profile_username}
        data = json.dumps(output_dict)

        #Put arguments into url header  
        req = urllib2.Request(url,data,{'Content-Type':'application/json'})

        #Attempt to retrieve profile.
        try:

            #Load json encoded profile. Give 3 seconds for other side to respond.
            data = urllib2.urlopen(req,timeout= 3).read()

            #Make sure object being returned is a json object
            try:

                loaded = json.loads(data)
                #Get relevant information from the profile.
                name = loaded.get('fullname','N/A')
                position = loaded.get('position','N/A')
                description = loaded.get('description','N/A')
                location = loaded.get('location','N/A')
                last_updated = loaded.get('lastUpdated','0')
                picture = str(loaded.get('picture','None'))


                #Open database to store the user profile information
                working_dir = os.path.dirname(__file__)
                db_filename = working_dir + "/db/userinfo.db"

                with open (db_filename,'r+'):
                    conn = sqlite3.connect(db_filename)
                    cursor = conn.cursor()

                cursor.execute("SELECT lastUpdated FROM Profile WHERE UPI = ?" , [profile_username])
                row = cursor.fetchall()

                #Check if picture is relative or absolute path, and perform 
                #necessary measures to get (or not get) the picture
                if ('http' not in picture and '/' in picture):
                    picture = ('http://%s:%s%s' % (ip,port,picture))

                elif('http' in picture):
                    pass
                else:
                    picture = 'None'


                #Insert new user information if new, otherwise update existing profile
                if (len(row) == 0):
                    cursor.execute("INSERT INTO Profile(UPI,Name,Position,Description,Location,Picture,lastUpdated) VALUES (?,?,?,?,?,?,?)",[profile_username,name,position,description,location,picture,last_updated])
                else:
                    #If retrieved profile is more updated than the one stored in database, update the profile
                    if (float(str(row[0][0])) < float(last_updated)):
                        cursor.execute("UPDATE Profile SET UPI = ?,Name = ?,Position = ?,Description = ?,Location = ?,Picture = ?, lastUpdated = ? WHERE UPI = ?" , [profile_username,name,position,description,location,picture,last_updated,profile_username])


                if ('http' in picture):
                    #Attempt to save the profile image from the given url.
                    try:
                        urllib.urlretrieve(picture, working_dir + "/serve/serverFiles/profile_pictures/"+profile_username+".jpg")
                        pic = ("/static/serverFiles/profile_pictures/%s.jpg" % (profile_username))
                        cursor.execute("UPDATE Profile SET Picture = ? WHERE UPI = ?" , [pic,profile_username])
                    except urllib2.URLError,exception:
                        pic = 'None'
                        cursor.execute("UPDATE Profile SET Picture = ? WHERE UPI = ?" , [pic,profile_username])
                        users.log_error("Failed to retrieve profile picture in /view_profile for %s | Reason : URL Error during retrieval, URL Error : %s" % (profile_username,exception))

                #Save database changes
                conn.commit()
                conn.close()

                page = read_HTML('/html/otherProfile.html')
                page = page.replace('DESTINATION_HERE',destination)
                page = page.replace('NAME_HERE',name)
                page = page.replace('POSITION_HERE',position)
                page = page.replace('DESCRIPTION_HERE',description)
                page = page.replace('LOCATION_HERE',location)
                page = page.replace('PICTURE_HERE',picture)

                return page

            except TypeError as exception:
                users.log_error("Failed to retrieve profile picture in /view_profile for %s | Reason : Type Error : %s" % (profile_username,exception))
                return 'Sorry, we couldn\'t fetch this profile. Please try again later.'

        #In case API call fails.
        except urllib2.URLError,exception:
            users.log_error("Failed to retrieve profile in /view_profile for %s | Reason : URL Error, Exception : %s" % (profile_username,exception))
            return 'Sorry, we couldn\'t fetch this profile. Please try again later.'


    except KeyError:

        return 'Session Expired'




        
""" This helper function returns a string of html
    Input : html_path (string, relative path of the html)
    Output : page (string, a string of html code to be displayed on the browser)
    """
def read_HTML(html_path):

    working_dir = os.path.dirname(__file__)
    filename = working_dir + html_path

    with open (filename,'r') as file:
        page = file.read()
        file.close()

    return page





"""This function(API) allows other users to request profile information for anyone from this client
    Input : data (dictionary, contains the username of the requested profile and the requester)
    Output : out (json encoded dictionary, contains information for the requested profile)
    """
def get_profile(data):

    #Try block; in case the API caller didn't add the compulsory input arguments
    try:

        #Extract inputs for this API call
        profile_username = data['profile_username']
        sender = data['sender']

        #Open database for extracting profile
        working_dir = os.path.dirname(__file__) 
        db_filename = working_dir + "/db/userinfo.db"
        with open (db_filename,'r'):
            conn = sqlite3.connect(db_filename)
            cursor = conn.cursor()

        #Read database and see if requested profile exists
        cursor.execute("SELECT Name,Position,Description,Location,Picture,lastUpdated FROM Profile WHERE UPI = ?" , [profile_username])
        row = cursor.fetchone()

        #Construct URL for image
        url = ("http://%s:%s%s" % (host_IP,port,row[4]))

        conn.close()

        #Check if profile exists in the database
        if (len(row) != 0):

            #Extract profile information in the rows and store it into a dictonary object to json encode later
            output_dict = {'fullname' :row[0],'position': row[1],'description': row[2],'location': row[3],'picture': url,'lastUpdated':row[5]}

            #Json encode the output dictionary then return it
            out = json.dumps(output_dict)
            return out

        else:
            users.log_error("Failed profile retrieval attempt for %s by %s | Reason : Profile does not exist" % (profile_username,sender))

    #Return error code 1 : Missing compulsory field
    except KeyError:

        return '1'



"""This function returns the profile page for the currently logged in user
    Input : None
    Output : page (string, a string of html code to be displayed on the browser)
    """
def view_own_profile():

    #Check session
    try:

        username = cherrypy.session['username']

        #Read database
        working_dir = os.path.dirname(__file__)
        db_filename = working_dir + "/db/userinfo.db"
        with open (db_filename,'r'):
            conn = sqlite3.connect(db_filename)
            cursor = conn.cursor()

        cursor.execute("SELECT Name, Position, Description,Location,Picture FROM Profile where UPI = ?" , [username])

        rows = cursor.fetchall()
            
        name = str(rows[0][0])
        position = str(rows[0][1])
        description = str(rows[0][2])
        location = str(rows[0][3])
        picture = str(rows[0][4])

        page = read_HTML('/html/ownProfile.html')
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



"""This function updates the profile information for the currently logged in user
    Inputs : name (string)
            position (string)
            description (string)
            location (string)
    Output : None
    """
def save_edit(name,position,description,location):
    
    #Check user session
    try:

        username = cherrypy.session['username']  

        #Prepare database for writing to
        working_dir = os.path.dirname(__file__)
        db_filename = working_dir + "/db/userinfo.db"
        with open(db_filename,'r+'):
            conn = sqlite3.connect(db_filename)
            cursor = conn.cursor()

        #Key for last updated profile
        lastUpdated = str(time.time())

        cursor.execute("UPDATE Profile SET Name = ?,Position =?,Description = ?,Location = ? ,lastUpdated = ? WHERE UPI = ?" , [name,position,description,location,lastUpdated,username])

        #Save database changes and return to userpage
        conn.commit()
        conn.close()

        raise cherrypy.HTTPRedirect('/view_own_profile')

    #Redirect to index
    except KeyError:

        raise cherrypy.HTTPRedirect('/')



"""This function updates the profile picture for the currently logged in user
    Input : picture (file data type)
    Output : None
    """
def edit_picture(picture):

    #Check session
    try:
        username = cherrypy.session['username']

        #Guess an extension for the file type
        fileType = mimetypes.guess_type(str(picture))

        #Prepare file path to store on server
        working_dir = os.path.dirname(__file__)
        new_filename = working_dir + "/serve/serverFiles/profile_pictures/" + username + ".jpg"

        #Write the uploaded data to a file and store it on the server
        if picture.file: 
            with file(new_filename, 'wb') as outfile:
                outfile.write(picture.file.read())

        #Prepare database for writing to
        db_filename = working_dir + "/db/userinfo.db"
        with open (db_filename,'r+'):
            conn = sqlite3.connect(db_filename)
            cursor = conn.cursor()

        picture = ("/static/serverFiles/profile_pictures/%s.jpg" % (username))

        cursor.execute("UPDATE Profile SET Picture = ? WHERE UPI = ?", [picture,username])

        #Save database changes and return to userpage
        conn.commit()
        conn.close()

        raise cherrypy.HTTPRedirect('/view_own_profile')

    except KeyError:
        raise cherrypy.HTTPRedirect('/')
