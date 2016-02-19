# General Reader class
# Could be RFID token reader or otherwise
class reader():
	
	def	__init__(self, parent, name):
		self.parent = parent
		self.name =	name
		self.function = None
		
	def	setFunction(self, function):
		self.function = function
		
	def	setAssociatedDoor(self,	associatedDoor):
		self.associatedDoor	= associatedDoor