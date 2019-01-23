# Light control class, responsible for activating the illumination and send an alert when the light sensor and the light are incoherent
# corrections at column 105

import time
import datetime

class LightControl:

	def __init__(self):

		self.status = None
		self.light = None
		self.dawn = None
		self.dusk = None

	def dawn_read(self):									# RETURN THE DAWN VALUE
		
		return str(self.dawn)
		
	def dusk_read(self):									# RETURN THE DUSK VALUE
		
		return str(self.dusk)

	def l_setting(self,light):								# UPDATE THE LIGHT SENSOR STATUS FROM SENML
		
		light_value = ((light["e"])[0])["v"]
		if (light_value == "ON"):																		# is needed "ON"/"OFF" or it could be 0/1?
			self.light = 1
		else:
			self.light = 0

	def l_ref_setting(self, dawn="Null", dusk="Null"):		# SET ILLUMINATION PERIOD
		
		self.dawn = dawn
		self.dusk = dusk
		
		if (dawn == "Null" or dusk == "Null"):
			condition = None
		else:
			date = time.ctime(time.time())										# 'Fri Jan 11 15:05:29 2019'
			time_form = date.split(" ")[3]										# '15:05:29'
			hour = float(time_form.split(":")[0] + time_form.split(":")[1])		# 1505
			dawn = float(def_dawn.split(":")[0] + def_dawn.split(":")[1])				# 0820  (08:20)
			dusk = float(def_dusk.split(":")[0] + def_dusk.split(":")[1])		# 2015  (20:15)
			
			if (hour >= dawn and hour <= dusk):
				condition = "day"
			else:
				condition = "night"

		self.status = condition

	def light_control(self):								# LIGHT CONTROL

		if (self.status == None):
			l_command = None								# check if this correspond to not publishing
		elif (self.status == "day"):
			l_command = 1
		else:
			l_command = 0
																										# following 7 light needed if I publish only one topic for the light
		l_alert = 1
		if (self.status == None):
			l_alert = None									# check if this correspond to not pubilshing
		elif (self.light == l_command):
			l_alert = 0
		
		light_out = {"light command":l_command,"light alert":l_alert}
		return light_out
		
	# def light_alert(self):									# LIGHT ALERT
		
		# command = self.light_control()
		# l_alert = 1
		
		# if (self.status == None):
			# l_alert = None									# check if this correspond to not pubilshing
		# elif (self.light == command):
			# l_alert = 0
			
		# return l_alert