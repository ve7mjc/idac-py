#!/usr/bin/python

# Commands IP -> Lock
COMMAND_POLL = "000";
COMMAND_LOCK = "011";
COMMAND_UNLOCK = "012";
COMMAND_CHECK_STATUS = "015";
COMMAND_CHECK_TIMING_LOCK = "050";
COMMAND_CHECK_TIMING_UNLOCK = "051";
COMMAND_DEBUG_MODE_ENABLE = "055";
COMMAND_DEBUG_MODE_DISABLE = "056";

# Responses from Lock Controller
RESPONSE_ACK = "500";
RESPONSE_ERROR = "501";
RESPONSE_FAULT_MECHANICAL_TIMEOUT = "502";
RESPONSE_STATUS_UNKNOWN = "510";
RESPONSE_STATUS_LOCKED = "511";
RESPONSE_STATUS_UNLOCKED = "512";
RESPONSE_MANUAL_LOCKED = "513";
RESPONSE_MANUAL_UNLOCKED = "514";
RESPONSE_KEYPAD_REQUEST_LOCK = "520";

import sys, os, urlparse
from fnmatch import fnmatch, fnmatchcase
import time
import socket

import paho.mqtt.client as paho
import json, pprint

import re

BUFFER_SIZE = 1024

# Check for commandline arguments
if (len(sys.argv) < 2):
	print("needs config; eg. rfid-reader.py config.json")
	exit()

# Check if config file supplied is accessible,
# otherwise quit
if not os.path.isfile(sys.argv[1]):
	print("cannot access " + sys.argv[1])
	exit()

# Load JSON configuration from disk
try:
	with open(sys.argv[1]) as data_file:
		config = json.load(data_file)
except:
	print("unable to process " + sys.argv[1])
	exit()

# Define event callbacks
def on_connect(mosq, obj, rc):
    pass

def on_message(mosq, obj, msg):
	if (msg.topic == "idac/" + clientName + "/command"):
		if (msg.payload == "lock"):
			lock()
		if (msg.payload == "unlock"):
			unlock()
	pass

def on_publish(mosq, obj, mid):
    pass

def on_subscribe(mosq, obj, mid, granted_qos):
    pass

def on_log(mosq, obj, level, string):
	pass

clientName = config["mqttClientName"]
mqttc = paho.Client(clientName)

# Assign event callbacks
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe

# Parse CLOUDMQTT_URL (or fallback to localhost)
url_str = os.environ.get('CLOUDMQTT_URL', 'mqtt://' + config["mqttRemoteHost"] + ":" + str(config["mqttRemotePort"]))
url = urlparse.urlparse(url_str)
mqttc.will_set('clients/' + clientName + '/status', 'offline', 1, True)
mqttc.connect(url.hostname, url.port)

mqttc.publish('clients/' + clientName + '/status', 'online', 1, True)

mqttc.loop_start()

#serviceStatus = {}
#serviceStatus["status"] = "healthy"
#serviceStatus["sub"] = {}
#serviceStatus["sub"]["serialip"] = {}
#serviceStatus["sub"]["serialip"]["description"] = "Serial Device Server"
#serviceStatus["sub"]["serialip"]["status"] = "healthy"
#serviceStatus["sub"]["anemometer"] = {}
#serviceStatus["sub"]["anemometer"]["description"] = "Ultrasonic Anemomometer"
#serviceStatus["sub"]["anemometer"]["depends"] = "serialip"

# should be able to get overall status easily
# clients/anemometer/status ["health"] = healthy
#def sitRep():
#    mqttc.publish("clients/" + clientName + "/status", serviceStatus["status"])
#    mqttc.publish("clients/" + clientName + "/fullstatus", json.dumps(serviceStatus))
#sitRep()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((config["socketHost"], config["socketPort"]))

lockStatus = "unknown"

# Start subscribe, with QoS level 0
mqttc.subscribe(str("idac/%s/command" % clientName))

def lock():
	lockStatus = "locking"
	writeLog("locking")
	sendCommand(COMMAND_LOCK)

def unlock():
	lockStatus = "unlocking"
	writeLog("unlocking")
	sendCommand(COMMAND_UNLOCK)

def sendCommand(command):
	s.sendall(str(command) + "\r\n")

def writeLog(message, level = "debug"):
	mqttc.publish("log/" + clientName + "/" + level, message)

# set socket mode to non-blocking
s.setblocking(0)
writeLog("initializing " + clientName)

# blocking loop with a KeyboardInterrupt exit
dataBuffer = ""
running = True
try:
    while running:
		
		mqttc.loop()
		
		# block for response from arduino
		try:
			data = s.recv(4096)
			dataBuffer = dataBuffer + data
			#print(data)
		except:
			pass
		#writeLog("received " + data + " from lock")

#        elements = data.split(",")
#        mqttc.publish(TARGET_TOPIC, '{"speed":"' + elements[0]+ '","direction":"' + elements[1] + '"}')
		time.sleep(0.1)

except KeyboardInterrupt:
	running = False
	print("Received keyboard interrupt.  Shutting down..")

# clean up socket
s.close()