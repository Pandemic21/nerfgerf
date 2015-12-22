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
		if get_row_exists('already_parsed', 'permalink', submission.permalink) is False:
			gen_log('Submission "' + submission.permalink + '" not parsed, parsing...')
			gen_log('Title: ' + submission.title)

			for keyword in keywords:	
				if keyword in submission.title:
					gen_log('"' + keyword + '" is in title')
					
					#insert it into already_parsed
					c.execute("INSERT INTO already_parsed VALUES (?)", (submission.permalink,))
					conn.commit()
					gen_log('Inserted into already_parsed successfully')
					
					#if the user already has exp (e.g. exists)...
					if get_row_exists('exp', 'user', str(submission.author)) is True:
						gen_log(str(submission.author) + ' already has EXP, increasing...')
						new_level = increase_exp(str(submission.author), keyword, '50')
						conn.commit()
					#if the user does not already have exp (e.g. does not exist)...
					else:
						gen_log(str(submission.author) + " does not exist, creating...")
						new_level = add_user(str(submission.author), keyword, '50')
						conn.commit()
					#did_level_up will be true (they did level up) or false (they did not level up)
					#if it is true we need to alert them
					if new_level is not -1:
						gen_log(str(submission.author) + ' leveled up to level ' + str(new_level) + ', alerting...')
						stats = get_stats(str(submission.author))
						avg_level = (int(stats[1]) + int(stats[4]) + int(stats[7])) / 3
						total_level = int(stats[1]) + int(stats[4]) + int(stats[7])
						post = 'You leveled up ' + keyword + ' to level ' + str(new_level) + '!\nAverage Level: ' + avg_level + '\nTotal Level: ' + total_level + '\nJinx: ' + stats[1] + ' (' + stats[3] + '/' + stats[2] + ')\nPost: ' + stats[4] + ' (' + stats[6] + '/' + stats[5] + ')\nBooty: ' + stats[7] + ' (' + stats[9] + '/' + stats[8] + ')'
						gen_log('Level up post = ' + post)
						#TODO uncomment this to alert users they leveled up
						#submission.add_comment(post)
				else:
					gen_log('"' + keyword + '" is NOT in title')
		else:
			gen_log('Submission "' + submission.permalink + '" already parsed, skipping...')

#returns True if the row exists (e.g. has already been entered in the DB)
#returns False if the row does not exist (e.g. has not been entered into the DB)
def get_row_exists(table, column, value):
	c.execute("SELECT count(*) FROM "+table+" WHERE "+column+"=?", (value,))
	data = c.fetchone()[0]
	if data==0:
		return False
	else:
		return True


#adds a user to the database
def add_user(user, exp_type, exp_amount):
	c.execute("INSERT INTO exp VALUES (?,?,?,?,?,?,?,?,?,?)", (user,'1','150','0','1','150','0','1','150','0',))
	gen_log('User created: ' + user)
	return increase_exp(user, exp_type, exp_amount)
	#TODO anything else when a user is created?


#increases a user's exp 
def increase_exp(user, exp_type, exp_amount):
	#get current exp	
	c.execute("SELECT "+exp_type+"_exp FROM exp WHERE user=?",(user,))
	current_exp = c.fetchone()[0]
	gen_log(user + " current exp: " + str(current_exp))
	
	#calculate new exp
	new_exp = int(current_exp) + int(exp_amount)
	gen_log(user + " new exp: " + str(new_exp))

	#determine if they leveled up
	c.execute("SELECT "+exp_type+"_cap FROM exp WHERE user=?",(user,))
	current_cap = c.fetchone()[0]
	
	#if they have not leveled up
	if int(current_exp) < int(current_cap):
		gen_log(user + " did not level up, current_cap = " + str(current_cap))
		c.execute("UPDATE exp SET "+exp_type+"_exp="+str(new_exp)+" WHERE user=?", (user,))
	#if they have leveled up
	else:
		gen_log(user + " leveled up, current_cap = " + str(current_cap))
		c.execute("UPDATE exp SET "+exp_type+"_exp=0 WHERE user=?", (user,))
		#get their current level and increase it by 1
		c.execute("SELECT "+exp_type+"_level FROM exp WHERE user=?",(user,))
		current_level = c.fetchone()[0]
		new_level = int(current_level) + 1
		gen_log(user + ' current_level = ' + str(current_level) + ', new_level = ' + str(new_level))
		#update their level to the new level
		c.execute("UPDATE exp SET "+exp_type+"_level="+str(new_level)+" WHERE user=?", (user,))

		#update their level cap to the new level cap
		#150 = minimum exp needed to level up (i.e. level 1-10 = 150 exp)
		#10  = level range (i.e. level 1-10 = 150 and 11-20 = 200, there's 10 difference between 20 and 10)
		new_level_cap = get_level_cap(new_level, 150, 10)
		c.execute("UPDATE exp SET "+exp_type+"_cap="+str(new_level_cap)+" WHERE user=?", (user,))

		#not -1 = they did level up and their new level is the number returned
		return int(new_level)
	#-1 = they did not level up
	return -1


#gets the level cap
def get_level_cap(current_level, level_cap, level_range):
	while current_level > level_range:
		level_cap = level_cap + 50
		level_range = level_range + 10
	return level_cap

#returns an array of their information
def get_stats(user):
	c.execute("SELECT * FROM exp WHERE user=?",(user,))
	#returns array
	#0 = user, 
	#1 = jinx_level, 2 = jinx_cap, 3 = jinx_exp, 
	#4 = post_level, 5 = post_cap, 6 = post_exp, 
	#7 = booty_level, 8 = booty_cap, 9 = booty_exp
	return c.fetch()


#logs to the log file
#log file is "nerfgerf.log" in the current directory
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

#if you update the keywords make sure you update the CREATE TABLE statement too
keywords = ['jinx', 'post', 'booty']

username = 'BOT_NAME_HERE'
password = 'PASSWORD_HERE'
#r.login(username, password)

#sqlite3 initialization
c.execute("CREATE TABLE IF NOT EXISTS exp (user text, jinx_level text, jinx_cap text, jinx_exp text, post_level text, post_cap text, post_exp text, booty_level text, booty_cap text, booty_exp text)")
c.execute("CREATE TABLE IF NOT EXISTS already_parsed (permalink text)")
conn.commit()

while True:
	parse_new(r, 'nerfgerf', 10)
	gen_log('Completed cycle, sleeping...')
	gen_log('###########################################################################################')
	time.sleep(30)
