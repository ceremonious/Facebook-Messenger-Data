import re
import os
import sys
import json
import urllib
import requests
import operator
from datetime import datetime
from collections import Counter
from bs4 import BeautifulSoup as bs

#Type in your info here
username = "" #Your facebook username
password = "" #Your facebook password
my_id = 0 #Your facebook id (See read me)
friends = [(0, "")] #The id and name of any friends. Ex: ([(1231203, "Alice"), (123213, "Bob")])

#This is the value that is searched for when finding the seed message
#th is the most common two letter pairing in the English language
search_value = "th"
#The number of messages received from Facebook each time
message_limit = 2000

#POST headers
headers = {'Host': 'www.facebook.com',
		   'Origin':'http://www.facebook.com',
		   'Referer':'http://www.facebook.com/',
		   'User-Agent': '"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.122 Safari/537.36'
		   }

if username == "" or password == "" or my_id == 0:
	print "Fill in your Facebook information"
	sys.exit(1)

#Log in to Facebook with the given username and password
def login(session, username, password):
	base_url = "https://www.facebook.com/"
	login_url = "https://www.facebook.com/login.php?login_attempt=1"
	home_request = session.get(base_url).text
	login_soup = bs(home_request, "lxml")
	lsd = str(login_soup.find_all('input', attrs={"name": "lsd"})[0]['value'])
	#Login data for the Login POST request
	login_data = {
	    'locale': 'en_US',
	    'non_com_login': '',
	    'email': username,
	    'pass': password,
	    'lsd': lsd
	}
	#Log in
	content = session.post(login_url, data=login_data, verify=False)
	return content

#Gets the ID of the first message with the search_value
def getSeedMessageID(otherID):
	url = "https://www.facebook.com/ajax/mercury/search_snippets.php?dpr=3"
	form = {
		"query":search_value,
		"snippetOffset":0,
		"snippetLimit":5,
		"other_user_fbid":otherID,
		"identifier":"thread_fbid",
		"client":"messenger",
		"__user":my_id,
		"__a":1,
		"__dyn":"7AzkXxaA4ojgDxyLqzGomzEbHGbGexuhLFwgoqwWhE98nwgUaoepovHgy3q2OUuKexK2K3ucDBwJx62i2PxOcG4K1Zxa2m4oqyUf8oCK251G6XDxW10wkotwVwlohCK6o98K6U6OfBwHx-8xubxy1by8sxeEgzU6WK6u4o",
		"__af":"h0",
		"__req":"17",
		"__be":"1",
		"__pc":"PHASED:DEFAULT",
		"__rev":3355945,
		"fb_dtsg":"AQHRyEnZUt-h:AQHGwIXiG0bm",
		"jazoest":2658172821216911090851164510458658172711197388105714898109,
		"__spin_r":3355945,
		"__spin_b":"trunk",
		"__spin_t":1507485173
	}
	seedData = session.post(url, headers=headers, data=form, verify=False).text
	message_dict = json.loads(seedData[9:])
	return message_dict["payload"]["search_snippets"][search_value][str(otherID)]["snippets"][0]["message_id"]

#Given a message, get all messages in the given direction
def getMessagesFromMessage(messageID, otherID, direction):
	url = "https://www.facebook.com/ajax/mercury/search_context.php?dpr=3"
	form = {
		"message_id":messageID,
		"limit":message_limit,
		"direction":direction,
		"other_user_fbid":otherID,
		"__user":my_id,
		"__a":1,
		"__dyn":"7AzkXxaA4ojgDxyLqzGomzEbHGbGexuhLFwgoqwWhE98nwgUaoepovHgy3q2OUuKexK2K3ucDBwJx62i2PxOcG4K1Zxa2m4oqyUf8oCK251G6XDxW10wkotwVwlohCK6o98K6U6OfBwHx-8xubxy1by8sxeEgzU6WK6u4o",
		"__af":"h0",
		"__req":"17",
		"__be":"1",
		"__pc":"PHASED:DEFAULT",
		"__rev":3355945,
		"fb_dtsg":"AQHRyEnZUt-h:AQHGwIXiG0bm",
		"jazoest":2658172821216911090851164510458658172711197388105714898109,
		"__spin_r":3355945,
		"__spin_b":"trunk",
		"__spin_t":1507485173
	}
	data = session.post(url, headers=headers, data=form, verify=False).text
	return json.loads(data[9:])

def get_message_history(session, my_id, friend_id, friendName):
	output = open(friendName + ".json", 'w')
	my_id = int(my_id)
	friend_id = int(friend_id)
	num_messages = 0
	messages = []

	seedurl = "https://www.facebook.com/ajax/mercury/search_context.php?dpr=3"
	seedMessage = getSeedMessageID(friend_id)
	currentMessageID = seedMessage
	direction = "down";

	while True:
		messageData = getMessagesFromMessage(currentMessageID, friend_id, direction)
		try:
			message_list = messageData['payload']['mercury_payload']['actions']
		except KeyError:
			#First get all messages in the downward direction
			#Then change directions and start going upwards
			if direction == "down":
				direction = "up"
				currentMessageID = seedMessage
				messageData = getMessagesFromMessage(currentMessageID, friend_id, direction)
				message_list = messageData['payload']['mercury_payload']['actions']
			#If both directions have been traversed, the loop terminates
			else:
				break

		#If going upwards, the next message is at the top
		#If going downwards, the next message is at the bottomn
		nextID = 0 if direction == "up" else len(message_list) - 1
		currentMessageID = message_list[nextID]["message_id"]

		num_messages += len(message_list)
		print str(num_messages) + " messages loaded."

		if direction == "up":
			message_list = reversed(message_list)

		for message in message_list:
			#Gets the content of the message
			try:
				message_content = message['body'].replace('\t', ' ').replace('\n', ' ')
			except KeyError:
				message_content = message['log_message_body'].replace('\t', ' ').replace('\n', ' ')

			#Gets when the message was sent
			message_id = message['message_id']
			sent = str(message['timestamp'])

			#Gets the device the message was sent from
			source = ' '.join(message['source_tags'])
			if 'mobile' in source:
				source = 'mobile'
			else:
				source = 'chat'

			#Gets who sent the message
			author = int(message['author'].split(':')[1])
			if author == my_id:
				sender = 'me'
			else:
				sender = friendName

			out = {'sender': sender, 'content': message_content, 'source': source, 'sent': sent}

			currentmessage = message_id

			#If going up, append. If going down, prepend.
			#This preserves the order of the messages
			try:
				if direction == "up":
					messages.append(out)
				else:
					messages.insert(0, out)
			except UnicodeEncodeError:
				out['content'] = out['content'].encode('unicode_escape').decode()
				if direction == "up":
					messages.append(out)
				else:
					messages.insert(0 ,out)

	#Write all the messages to a file
	data = {messages: messages}
	output.write(json.dumps(data))
	output.close()
	return num_messages

#Start a session to log in to FB
session = requests.Session()
try:
	content = login(session, username, password)
except:
	print "Log in failed"
	sys.exit(1)

for friend in friends:
	friendID = int(friend[0])
	friendName = friend[1]
	print 'Getting message history for: ' + friendName
	num_messages = get_message_history(session, my_id, friendID, friendName)
	print str(num_messages) + ' with ' + friendName
