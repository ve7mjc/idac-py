# Requires hardware channel number and is hardcoded to a distio
# piface implementation
# 
# Doors can have an automatic lock window which means it will be
# locked by default during these times.  Unlock requests result
# in a pulse for the desired time and return to a locked status
# Doors can have a permanent auto lock status which remains locked
# by default at all times
#

import datetime

class door():

	def	__init__(self, parent, name, hwChannel,	description=None):
		self.parent = parent
		self.name =	name
		self.hwChannel = hwChannel
		if description is not None:	self.description = description
		else: self.description = self.name
		self.unlockPulseTimeMs = 6000
		
		self.autoLockTimeEnabled = False
		self.autoLockEnabled = False

		# status tracking		
		self.locked = False

	def setAutoLockTime(self, start_hour, start_minute, end_hour, end_minute):
		self.start_hour = int(start_hour)
		self.start_minute = int(start_minute)
		self.end_hour = int(end_hour)
		self.end_minute = int(end_minute)
		self.autoLockTimeEnabled = True
		
	def setAutoLock(self, value):
		self.autoLockEnabled = value

	def inAutoLockTimeWindow(self):
		
		# if AutoLockEnabled is true, this applies
		# to all times, so return in affirmative
		if self.autoLockEnabled:
			return True
		
		if self.autoLockTimeEnabled:
			# set up datetime objects for comparison
			now = datetime.datetime.now()
			autoLockTimeStart = now.replace(hour=self.start_hour, minute=self.start_minute, second=0, microsecond=0)
			autoLockTimeEnd = now.replace(hour=self.end_hour, minute=self.end_minute, second=0, microsecond=0)
	
			# if the current time falls within the auto-lock time frame
			# then lock the door if it is unlocked
			if (autoLockTimeStart < now) or (now < autoLockTimeEnd):
				return True
			else: return False
				
		else:
			# autoLockTimeEnabled is false, thus the time is
			# irrelevant
			return False

	def checkAutoLock(self):
		return self.inAutoLockTimeWindow()
		
	def isLocked(self):
		return self.locked

	# Unlock the door either latched or momentary depending on 
	# auto-lock configuration and time of day
	def	unlock(self):
		if (not self.autoLockEnabled) and (not self.inAutoLockTimeWindow()):
			self.parent.writeLog("unlocking {0}".format(self.name, "notice"))
			self.parent.mqttc.publish("io/piface/dio-output/{0}/set/state".format(self.hwChannel), "1")
			self.locked = False
		else:
			self.unlock_pulse(self.unlockPulseTimeMs)
		
	def	unlock_pulse(self, timeMs =	6000):
		self.parent.mqttc.publish("io/piface/dio-output/{0}/set/pulse".format(self.hwChannel), str(timeMs))
		self.parent.writeLog("unlocking {0} for {1} mS".format(self.name, timeMs))
	
	def	lock(self):
		self.parent.mqttc.publish("io/piface/dio-output/{0}/set/state".format(self.hwChannel), "0")
		self.parent.writeLog("locking {0}".format(self.name))
		self.locked = True