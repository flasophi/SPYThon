# Control class, responsible for reacting to the inputs from the device connector
# corrections at column 105

import time
import datetime

class Control:

	def __init__(self):

		self.status = None
		self.temp = None
		self.t_ref = None
		self.hum = None
		self.h_ref = "62.5"
		self.light = None
		self.dawn = None
		self.dusk = None
	
	def catalogip(self):									# RETRIEVE CATALOG IP
	
		file = open("conf.txt","r")
		data = json.loads(file.read())
		catalogip = data["catalogip"]
		file.close()
		return catalogip
	
	def deviceID(self):										# RETRIVE ASSOCIATED DEVICEID (TERRARIUM)
		
		file = open("conf.txt","r")
		data = json.loads(file.read())
		deviceID = data["deviceID"]
		file.close()
		return deviceID

	def temp_read(self):									# RETURN THE TEMPERATURE VALUE
		
		return srt(self.temp)
		
	def dawn_read(self):									# RETURN THE DAWN VALUE
		
		return str(self.dawn)
		
	def dusk_read(self):									# RETURN THE DUSK VALUE
		
		return str(self.dusk)
		
	def t_setting(self,temp):								# UPDATE THE TEMPERATURE
		
		self.temp = temp
	
	def h_setting(self,hum):								# UPDATE THE HUMIDITY
	
		self.hum = hum
		
	def l_setting(self,light):								# UPDATE THE LIGHT SENSOR STATUS
	
		self.light = light									# check what is coming as input (snml?)
		
	def t_ref_setting(self,t_ref="Null"):					# SET THE REFERENCE TEMPERATURE
		
		if (t_ref == "Null"):
			self.t_ref = None
		else:
			self.t_ref = t_ref
	
	def l_ref_setting(self,dawn="Null",dusk="Null"):		# SET ILLUMINATION PERIOD
		
		self.dawn = dawn
		self.dusk = dusk
		
		if (dawn == "Null" or dusk == "Null"):
			condition = None
		else:
			date = time.ctime(time.time())										# 'Fri Jan 11 15:05:29 2019'
			time_form = date.split(" ")[3]										# '15:05:29'
			hour = float(time_form.split(":")[0] + time_form.split(":")[1])		# 1505
			dawn = float(.split(":")[0] + def_dawn.split(":")[1])				# 0820  (08:20)
			dusk = float(def_dusk.split(":")[0] + def_dusk.split(":")[1])		# 2015  (20:15)
			
			if (hour >= dawn and hour <= dusk):
				condition = "day"
			else:
				condition = "night"

		self.status = condition
		
	def temp_control(self):									# TEMPERATURE CONTROL
	
		if (self.t_ref == "Null"):
			t_command = None																			# check if this correspond to not publishing
		else:	
			if (self.status == None):
				
				if (self.light == "1"):						# temperature control without light control
					t_inf = float(self.t_ref) - 1
					t_sup = float(self.t_ref) + 1
				else:
					t_inf = float(self.t_ref) - 5
					t_sup = float(self.t_ref) - 3
					
			elif (self.status == "day"):					# temperature control with light control
				t_inf = float(self.t_ref) - 1
				t_sup = float(self.t_ref) + 1
			else:
				t_inf = float(self.t_ref) - 5
				t_sup = float(self.t_ref) - 3
			
			if (self.temp <= t_inf):
				t_command = "1"
			if (self.temp >= t_sup):
				t_command = "0"
	
		return t_command
		
	def light_control(self):								# LIGHT CONTROL

		if (self.status == None):
			l_command = None								# check if this correspond to not publishing
		elif (self.status == "day"):
			l_command = "1"
		else:
			l_command = "0"
		
		return l_command
		
	def light_alert(self):									# LIGHT ALERT
		
		command = self.light_control()
		l_alert = "1"
		
		if (self.status == None):
			l_alert = None									# check if this correspond to not pubilshing
		elif (self.light == command):
			l_alert = "0"
			
		return l_alert
		
	def hum_alert(self):									# HUMIDITY ALERT
		
		h_inf = float(self.h_ref) - 3.0
		h_sup = float(self.h_ref) + 3.0
		
		if (float(self.hum) <= h_inf or float(self.hum) >= h_sup):
			h_alert = "1"
		else:
			h_alert = "0"
	
		return h_alert