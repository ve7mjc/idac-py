#!/usr/bin/python3

import urllib.parse
import urllib.request
import datetime

# idac controller
#

from idac_client import *
from idac_reader import reader
from idac_door import door

class idac(idac_client):
	
	def	mqttMessage(self, topic, payload):

		# process token	against	appropriate	rfid reader
		match =	re.search("idac/reader/([^/]*)/token-detected", topic)
		if match:
			self.processToken(match.group(1), payload)

		# process token	against	appropriate	rfid reader
		match =	re.search("io/([^/]*)/dio-input/([^/]*)/state", topic)
		if match:
			self.processDistioInputs(match.group(1), match.group(2), payload)

	def	sendTelemetry(self,	token, reader, eventType):
		
		# assemble HTTP POST url encoded string
		data = urllib.parse.urlencode({
			'reader_name'	: reader,
			'token_code'	: token["code"],
			'event_type'	: eventType,
			'member_id'		: token["userId"],
			'token_id'		: token["id"],
		}).encode('ascii')
		
		# we are not currently reading the response but
		# should as it is our only feedback from the portal
		req = urllib.request.Request("{0}logAccessEvent".format(self.config["apiUrl"]), data)
		with urllib.request.urlopen(req) as response:
   			resp = response.read()
	
	# process incoming distio input states
	def processDistioInputs(self, device, channel, state):
		
		# front lock button
		if (channel == "0") and (state == "0"):
			self.writeLog("last maker out declared", "notice")
			self.doors["front-entrance"].lock()

	def	processToken(self, reader, tokenCode):
		
		self.writeLog("processing token {0} from {1}".format(tokenCode,reader),	"debug")

		# Reject if token not known
		if tokenCode not in self.tokens:
			self.writeLog("unknown token detected {0} at {1}".format(tokenCode, reader), "notice")
			self.mqttc.publish("ivy", "TOKEN REJECTED")
			return True

		## Process Token
		if self.readers[reader].function == "lock":
			if self.tokens[tokenCode]["access"] is ACCESS_PERMITTED:
				self.doors[self.readers[reader].associatedDoor].unlock()
				self.writeLog("granted access to {0}({1}) via {2}".format(self.tokens[tokenCode]["userName"], self.tokens[tokenCode]["code"], reader), "notice")
				#self.sendTelemetry(self.tokens[tokenCode], reader, EVENT_ACCESS_GRANTED)
			else:
				self.writeLog("denied access to	{0}({1}) via {2}".format(self.tokens[tokenCode]["userName"], self.tokens[tokenCode]["code"], reader), "notice")
				#self.sendTelemetry(self.tokens[tokenCode], reader, EVENT_ACCESS_DENIED)
		elif self.readers[reader].function == "exit":
			self.writeLog("leave requested by {0}({1}) via {2}".format(self.tokens[tokenCode]["userName"], self.tokens[tokenCode]["code"], reader), "notice")
			self.sendTelemetry(self.tokens[tokenCode], reader, EVENT_EXIT_REQUESTED)
		else:
			self.writeLog("token {0}({1}) via {2} but nothing to do".format(self.tokens[tokenCode]["userName"], self.tokens[tokenCode]["code"], reader), "notice")

	def	loadTokens(self):

		if os.path.isfile(self.config["tokenPath"]):
			self.lastTokenDatModified =	os.stat(self.config["tokenPath"]).st_mtime
			try:
				with open(self.config["tokenPath"])	as data_file:
					newTokens =	{}
					for	line in	data_file:
						try:
							token =	{}
							elm	= line.split(',')
							token["code"] =	elm[0]
							token["id"]	= elm[1]
							token["userId"]	= elm[2]
							token["access"]	= int(elm[3])
							token["userName"] =	elm[4]
							newTokens[token["code"]] = token
						except:
							writeLog("error	processing token line: " + line, "error")
					if len(newTokens):
						self.tokens	= newTokens
						self.writeLog("read " + str(len(self.tokens)) + " access tokens", "notice")
			except:
				self.writeLog("error loading tokens from disk",	"error")
		else:
			self.writeLog("unable to locate or access token file {0}".format(self.config["tokenPath"]), "error")
	
	def	checkNewTokens(self):
		try:
			if os.stat(config["tokenPath"]).st_mtime > lastTokenDatModified:
				# check	for	actual change by hashing file and checking fingerprint
				self.loadTokens()
				self.writeLog("new token dat detected; loading")
		except:
			pass # quiet errors	for	now, the old silent	fail
			
	# check all known doors to see if they are configured for auto lock
	# and if they should be
	def checkAutoLocks(self):
		for key in self.doors:
			if self.doors[key].checkAutoLock() and not self.doors[key].isLocked():
				self.writeLog("locking door {0} automatically as auto lock time window has begun".format(key))
				self.doors[key].lock()

	def	run(self):
		
		# global vars and lists
		self.tokens	= {}
		self.doors = {}
		self.readers = {}
		
		self.loadTokens()

		# hard coded prototyping
		# this should be stored	in a db	or config
		frontEntranceDoor =	door(self, "front-entrance", 0, "Front Door")
		frontEntranceDoor.setAutoLockTime(19,20,8,0)
		self.doors["front-entrance"] = frontEntranceDoor
		frontEntranceReader	= reader(self, "front-entrace")
		frontEntranceReader.setFunction("lock")
		frontEntranceReader.setAssociatedDoor("front-entrance")
		self.readers["front-entrance"] = frontEntranceReader
		frontExitReader	= reader(self, "front-exit")
		frontExitReader.setFunction("exit")
		self.readers["front-exit"] = frontExitReader
		
		# Bus Subscriptions
		self.mqttc.subscribe("idac/#", QOS_EXACTLY_ONCE)
		self.mqttc.subscribe("io/#", QOS_EXACTLY_ONCE)
		#self.mqttc.subscribe("alarm/#", QOS_EXACTLY_ONCE)
		
		timer1Hz = time.time() + 1 # set for 1 second from now

		while True:
	
			self.processMqttMessages()
	
			# 1Hz Periodic Task	Timer
			if timer1Hz	<= time.time():		
				self.checkNewTokens()
				self.checkAutoLocks()
				timer1Hz = time.time() + 1
			
			time.sleep(0.005)

		
class Partition():
	
	def __init__(self, parent, name):
		self.parent = parent
		self.name = name
		



idac = idac()