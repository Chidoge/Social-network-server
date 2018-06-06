import sqlite3
import os

def create_message_db():

	working_dir = os.path.dirname(__file__)
	db_filename = working_dir + "/db/messages.db"

	with sqlite3.connect(db_filename) as conn:
		cursor = conn.cursor()
		cursor.execute("CREATE TABLE IF NOT EXISTS 'Messages'( Sender TEXT, Destination TEXT, Message TEXT, Stamp NUMERIC, isFile INTEGER)")
		cursor.execute("CREATE TABLE IF NOT EXISTS 'MessageBuffer'( Sender TEXT, Destination TEXT, Message TEXT, Stamp TEXT, isFile TEXT)")
		conn.commit()


def create_user_info_db():

	working_dir = os.path.dirname(__file__)
	db_filename = working_dir + "/db/userinfo.db"

	with sqlite3.connect(db_filename) as conn:
		cursor = conn.cursor()
		cursor.execute("CREATE TABLE IF NOT EXISTS 'UserList'(UPI TEXT, IP TEXT, PORT INTEGER, lastLogin NUMERIC, lastLimit NUMERIC DEFAULT 0, requestsPastMinute INTEGER DEFAULT 0)")
		cursor.execute("CREATE TABLE IF NOT EXISTS 'Profile'(UPI TEXT, Name TEXT, Position TEXT, Description TEXT, Location TEXT, Picture TEXT, lastUpdated NUMERIC)")
		conn.commit()



def set_up_all_db():
	create_message_db()
	create_user_info_db()
