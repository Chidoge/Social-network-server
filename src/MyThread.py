import datetime
import thread
from threading import Thread,Event
import urllib2
import time
import sys
import atexit
import cherrypy

listen_port = 10010


class MyThread(Thread):

    def __init__(self):
        Thread.__init__(self)
        self._stop_event = Event()


    def run(self):

        while not self._stop_event.wait(2):
            hostIP = urllib2.urlopen('https://api.ipify.org').read()
    	    r = urllib2.urlopen(thisURL).read()
    	    print r
            # call a function

    def stop(self):
    	
    	self._stop_event.set()
    	

    def setURL(self,url):
    	global thisURL
    	thisURL = url
