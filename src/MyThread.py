"""MyThread.py

    COMPSYS302 - Software Design
    Author: Lincoln Choy

    This thread class is used for regularly reporting to the login server.
    Currently does nothing else.
"""
import thread
from threading import Thread,Event
import urllib2


class MyThread(Thread):

    def __init__(self):
        Thread.__init__(self)
        self._stop_event = Event()


    def run(self):

        while not self._stop_event.wait(40):
    	    r = urllib2.urlopen(this_URL).read()


    def stop(self):

    	self._stop_event.set()


    def set_login_URL(self,url):
    	global this_URL
    	this_URL = url


