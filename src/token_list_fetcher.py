#!/usr/bin/python3

# token	getter

from idac_client import *

import urllib.request
import shutil
import hashlib

TOKEN_UPDATE_RATE = 1 * 10

class Tokens(idac_client):

	def init(self):
		
		# hash tokens on disk
		if os.path.isfile(self.config["tokenPath"]):
			with open(self.config["tokenPath"], 'rb') as data:
				tokenList = data.read()
		
			# Calculate MD5 hash of list
			self.hasher = hashlib.md5()
			self.hasher.update(tokenList)
			self.lastHashDigest = self.hasher.hexdigest()

		else:
			self.lastHashDigest = None

	def	getTokenList(self):
		
		# Retrieve token list
		with urllib.request.urlopen(self.config["tokenUrl"]) as response:
		    data = response.read()
		
		# Calculate MD5 hash of list
		self.hasher = hashlib.md5()
		self.hasher.update(data)
		newHashDigest = self.hasher.hexdigest()
		
		# Compare hashes and write to disk if determined new
		if newHashDigest != self.lastHashDigest:
			with open(self.config["tokenPath"], 'wb') as out_file:
				out_file.write(data)
			self.lastHashDigest = newHashDigest
			self.writeLog("updated token list downloaded", "notice")
			print(newHashDigest)
	
	def	run(self):

		self.timerTimeout =	TOKEN_UPDATE_RATE
		timer =	self.timerTimeout
		
		# Start	by getting tokens right	now
		self.getTokenList()

		while True:

			time.sleep(1)
			timer -= 1
			
			if (timer <= 0):
				timer =	self.timerTimeout
				self.getTokenList()

tokens = Tokens()