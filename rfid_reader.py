#!/usr/bin/python3

import socket

from idac_client import *

class rfid_reader(idac_client):
	
	def init(self):
		
		self.lastToken = ""
		self.lastTokenTime = time.time()
		self.dataBuffer = ""
		self.ignoreSameTokenTimeMs = 5000
		
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.config["socketHost"], self.config["socketPort"]))
		
		time.sleep(.005) # delay on the connect
		#self.sock.setblocking(0)
		
	def processToken(self, tokenCode):
		# ignore conditions
		if (tokenCode is self.lastToken) and ((time.time() - self.lastTokenTime) < self.ignoreSameTokenTimeMs):
			return False
		
		if (tokenCode is not self.lastToken):
			self.writeLog("detected token {0}".format(tokenCode))
			self.mqttc.publish("idac/reader/{0}/token-detected".format(self.config["mqttClientName"]), tokenCode)
			self.lastToken = tokenCode
			self.lastTokenTime = time.time()
	
	def processDataBuffer(self):

		line = ""
		# T:NACK 136 0 10 128 201\r\n>
		if "T:ACK" or "T:NACK" in self.dataBuffer:
			if "\r\n>" in self.dataBuffer:
				# lets trim from the front if necessary
				while self.dataBuffer[0] is not "T":
					self.dataBuffer = self.dataBuffer[1:]
				while (self.dataBuffer[0] != "\r"):
					line = line + self.dataBuffer[0]
					self.dataBuffer = self.dataBuffer[1:] # remove front byte
				# remove \r\n>
				while len(self.dataBuffer) and (self.dataBuffer[0] != "T"):
					self.dataBuffer = self.dataBuffer[1:]
				self.processLine(line)
				
	def processLine(self, line):
		# Example Token Event
		# T:NACK 136 0 10 128 201\n>
		try:
			el = line.split(" ")
			code = ""
			for i in range(1,len(el)):
				byte = hex(int(el[i]))[2:]
				if (len(byte) == 1):
					byte = "0" + byte
				code = code + byte
			self.processToken(code)
		except:
			self.writeLog("error processing \"{0}\" line".format(line), "error")
			return True
	
	def run(self):
		
		data = None
		while True:
			#try:
			data = self.sock.recv(4096)
			if len(data) > 0:
				self.dataBuffer = self.dataBuffer + data
				self.processDataBuffer()
			else:
				self.sock.connect((self.config["socketHost"], self.config["socketPort"]))

			#except:
			


reader = rfid_reader()