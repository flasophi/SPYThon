# Light control class, responsible for activating the illumination between hours set by the user
# corrections at column 105

import time
import datetime
import json

class LightControl:

	def __init__(self):

		self.status = None
		self.dawn = "null"
		self.dusk = "null"

	def dawn_read(self):									# RETURN THE DAWN VALUE
		
		return str(self.dawn)
		
	def dusk_read(self):									# RETURN THE DUSK VALUE
		
		return str(self.dusk)

	def l_ref_setting(self, dawn, dusk):		# SET ILLUMINATION PERIOD
		
		self.dawn = str(dawn)
		print ("dawn" + str(dawn))
		self.dusk = str(dusk)
		print ("dusk" + str(dusk))
		
	def light_control(self):								# LIGHT CONTROL

		if (self.dawn == "null" or self.dusk == "null"):
			self.status = "Deactivate"
			l_command = None
		else:
			self.status = "Active"
			date = time.ctime(time.time())													# 'Fri Jan 11 15:05:29 2019'
			elem = date.split(" ")
			for i in elem:
				if ":" in i:
					time_form = i															# '15:05:29'
			#time_form = date.split(" ")[4]
			#print time_form
			hour = int(str(time_form.split(":")[0]) + str(time_form.split(":")[1]))			# 1505
			dawn = int(str(self.dawn.split(":")[0]) + str(self.dawn.split(":")[1]))			# 0820  (08:20)
			dusk = int(str(self.dusk.split(":")[0]) + str(self.dusk.split(":")[1]))			# 2015  (20:15)
			#print "dawn = " + str(dawn) + ", dusk = " + str(dusk)
			
			if (hour == dawn):
				l_command = 1
				print "luce sia"
			elif (hour == dusk):
				l_command = 0
				print "notte dei tempi"
			else:
				l_command = None

		return l_command