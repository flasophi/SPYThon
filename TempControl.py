# Temperature control class, responsible for activating the heater and send alert when humidity goes out of range
# corrections at column 105

class TempControl:

	def __init__(self):

		self.status = None																				# see how to impose day/night
		self.temp = None
		self.t_ref = None
		self.hum = None
		self.h_ref = "62.5"

	def temp_read(self):									# RETURN THE TEMPERATURE VALUE
		
		return str(self.temp)
		
	def t_setting(self,temp):								# UPDATE THE TEMPERATURE FROM SENML
		
		self.temp = (temp["e"])["v"]
	
	def h_setting(self,hum):								# UPDATE THE HUMIDITY FROM SENML
	
		self.hum = ((hum["e"])[0])["v"]
		
	def t_ref_setting(self,t_ref="Null"):					# SET THE REFERENCE TEMPERATURE
		
		if (t_ref == "Null"):
			self.t_ref = None
		else:
			self.t_ref = t_ref
	
	def temp_control(self):									# TEMPERATURE CONTROL
	
		if (self.t_ref == "Null"):
			t_command = None																			# check if this correspond to not publishing
		else:
			# if (self.status == None):
				
				# if (self.light == "1"):						# temperature control without light control
					# t_inf = float(self.t_ref) - 1
					# t_sup = float(self.t_ref) + 1
				# else:
					# t_inf = float(self.t_ref) - 5
					# t_sup = float(self.t_ref) - 3
					
			# elif (self.status == "day"):					# temperature control with light control
				# t_inf = float(self.t_ref) - 1
				# t_sup = float(self.t_ref) + 1
			# else:
				# t_inf = float(self.t_ref) - 5
				# t_sup = float(self.t_ref) - 3
					
			t_inf = self.t_ref - 1																		#.#.#.!.!.!.#.#.#
			t_sup = self.t_ref + 1																		#.#.#.!.!.!.#.#.#
			
			if (self.temp <= t_inf):
				t_command = 1
			if (self.temp >= t_sup):
				t_command = 0
	
		return t_command

	def hum_alert(self):									# HUMIDITY ALERT
		
		h_inf = float(self.h_ref) - 3.0
		h_sup = float(self.h_ref) + 3.0
		
		if (self.hum <= h_inf or self.hum >= h_sup):
			h_alert = 1
		else:
			h_alert = 0
	
		return h_alert