import praw
import sqlite3
import time

#TODO fix TODOs


###########################################################################################
###########################################################################################
###########################################################################################

def parse_new(r, sub, num):
	subreddit = r.get_subreddit(sub)

	#get the latest submissions in the subreddit
	for submission in subreddit.get_new(limit=num):
		#make sure submission hasn't already been parsed...
		if get_row_exists('already_parsed', 'id', submission.id) is False:
			gen_log('Submission "' + submission.id + '" not parsed, parsing...')
			gen_log('Title: ' + submission.title)

			for keyword in keywords:	
				if keyword in submission.title:
					gen_log('"' + keyword + '" is in title')
					
					#insert it into already_parsed
					c.execute("INSERT INTO already_parsed VALUES (?)", (submission.id,))
					conn.commit()
					gen_log('Inserted into already_parsed successfully')
					
					#if the user already has exp (e.g. exists)...
					if get_row_exists('exp', 'user', str(submission.author)) is True:
						gen_log(str(submission.author) + ' already has EXP, increasing...')
						increase_exp(str(submission.author), keyword, '1')
						conn.commit()
					#if the user does not already have exp (e.g. does not exist)...
					else:
						gen_log(str(submission.author) + " does not exist, creating...")
						add_user(str(submission.author), keyword, '1')
						conn.commit()
				else:
					gen_log('"' + keyword + '" is NOT in title')
		else:
			gen_log('Submission "' + submission.id + '" already parsed, skipping...')


#returns True if the row exists (e.g. has already been entered in the DB)
#returns False if the row does not exist (e.g. has not been entered into the DB)
#table = the table to query (e.g. "original_submissions" or "repost_submissions")
def get_row_exists(table, column, value):
	c.execute("SELECT count(*) FROM "+table+" WHERE "+column+"=?", (value,))
	data = c.fetchone()[0]
	if data==0:
		return False
	else:
		return True


def add_user(user, exp_type, exp_amount):
	c.execute("INSERT INTO exp VALUES (?,?,?,?)", (user,'0','0','0',))
	print 'User created: ' + user
	#TODO anything else when a user is created?


def increase_exp(user, exp_type, exp_amount):
	c.execute("SELECT "+exp_type+" FROM exp WHERE user=?",(user,))
	current_exp = c.fetchone()[0]
	gen_log(user + " current exp: " + str(current_exp))
	new_exp = int(current_exp) + int(exp_amount)
	gen_log(user + " new exp: " + str(new_exp))
	c.execute("UPDATE exp SET "+exp_type+"="+str(new_exp)+" WHERE user=?", (user,))


def gen_log(data):
	f = open(logfile, 'a')
	datetime =  str(time.strftime("%Y/%m/%d")) + " " + str(time.strftime("%H:%M:%S"))
	f.write(datetime + ": " + data + "\n")
	f.close()
	print datetime + ": " + data

###########################################################################################
###########################################################################################
###########################################################################################

#variable initialization
r = praw.Reddit("/r/nerfgerf EXP keeper by /u/Pandemic21")
conn = sqlite3.connect('/home/pandemic/Documents/nerfgerf/nerfgerf.db')
c = conn.cursor()
logfile = "./nerfgerf.log"

#if you update the keywords make sure yo uupdate the CREATE TABLE statement too
keywords = ['encrypt', 'experience', 'dne']


#sqlite3 initialization
c.execute("CREATE TABLE IF NOT EXISTS exp (user text, encrypt text, experience text, dne text)")
c.execute("CREATE TABLE IF NOT EXISTS already_parsed (id text)")
conn.commit()

#r.login(username, password)

while True:
	parse_new(r, 'requestabot', 5)
	gen_log('Completed cycle, sleeping...')
	gen_log('###########################################################################################')
	time.sleep(30)
