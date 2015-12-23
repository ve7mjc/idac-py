import time
import os, sys
import re
import urllib
import queue

#from fnmatch import fnmatch, fnmatchcase
import json

import paho.mqtt.client as paho

# Constants from token datafile from members portal
# Number is assigned for level of access to token
ACCESS_DENIED = 1
ACCESS_PERMITTED = 2
ACCESS_LAPSED = 4

# Constants for Telemetry to api portal
EVENT_ACCESS_GRANTED = 1
EVENT_ACCESS_DENIED = 2
EVENT_EXIT_REQUESTED = 3
EVENT_DOOR_UNLOCKED = 4
EVENT_DOOR_LOCKED = 5

# MQTTC
QOS_AT_MOST_ONCE = 0
QOS_AT_LEAST_ONCE = 1
QOS_EXACTLY_ONCE = 2

class idac_client():

	def __init__(self):
		
		self.mqttMessages = queue.Queue()
		
		# return filesystem stat call times as float
		os.stat_float_times(False)
		
		# Default to automatically launching main runloop
		self.autoRun = True
		
		# calculate application base name and real application path
		self.scriptNameBase = sys.argv[0]
		if "." in sys.argv[0]:
			e = sys.argv[0].split(".")
			self.scriptNameBase = e[len(e)-2]

		self.appPath = os.path.dirname(os.path.realpath(sys.argv[0]))
		self.stateCacheFile = "{0}/{1}.cache".format(self.appPath, self.scriptNameBase)
		
		# Check for commandline arguments
		# Load config
		if (len(sys.argv) >= 2):
			if os.path.isfile(sys.argv[1]):
				configFilePath = sys.argv[1]
			else:
				print("cannot access configuration file {0}".format(sys.argv[1]))
				exit()
		else:
			if os.path.isfile("{1}.json".format(self.appPath, self.scriptNameBase)):
				configFilePath = "{1}.json".format(self.appPath, self.scriptNameBase)
			else:
				print("needs config; eg. {0} config.json".format(sys.argv[0]))
				exit()
			
		# Try to process config file	
		try:
			with open(configFilePath) as data_file:
				self.config = json.load(data_file)
		except:
			self.writeLog("unable to process configuration file {0}".format(configFilePath))
			
		self.mqttc = paho.Client(self.config["mqttClientName"])
		self.mqttc.on_message = self.on_message
		self.mqttc.on_connect = self.on_connect
		self.mqttc.on_publish = self.on_publish
		self.mqttc.on_subscribe = self.on_subscribe
		
		# call subclass init
		self.init()
		
		# Initialize and begin MQTT
		self.mqttc.will_set("clients/{0}/status".format(self.config["mqttClientName"], 'offline', 0, False))
		
		# Connect to MQTT Broker
		# we should do more to detect mqtt broker from env
		# or fallback to a localhost if not supplied
		self.mqttc.connect(self.config["mqttRemoteHost"], int(self.config["mqttRemotePort"]))
		self.mqttc.loop_start()

		# automatically begin mainloop unless
		# directed otherwise in reimplemented init() method
		if self.autoRun:
			try:
				self.run()
			except (KeyboardInterrupt, SystemExit):
				print("Received keyboard interrupt.  Shutting down..")

		
	# for reimplemenation
	def init(self):
		pass
		
	def run(self):
		pass
		
	def mqttMessage(self, topic, message):
		pass

	# MQTT Connected to Broker
	#
	def on_connect(self, *args, **kwargs):
		self.mqttc.publish("clients/{0}/status".format(self.config["mqttClientName"]),"online")
		self.mqttc.publish("logs/{0}/notice".format(self.config["mqttClientName"]), "started idac controller")
	
	# MQTT Message Received
	#
	def on_message(self, *args, **kwargs):
		topic = args[2].topic
		message = args[2].payload.decode('utf-8')
		# place mqtt messages in a thread-safe queue
		self.mqttMessages.put((topic,message))
		
	def processMqttMessages(self):
		while not self.mqttMessages.empty():
			(topic, message) = self.mqttMessages.get()
			self.mqttMessage(topic,message)
	
	def on_publish(self, *args, **kwargs):
	    pass
	
	def on_subscribe(self, *args, **kwargs):
	    pass
	
	def writeLog(self, message, level = "debug"):
		self.mqttc.publish("logs/" + self.config["mqttClientName"] + "/" + level.lower(), message)
