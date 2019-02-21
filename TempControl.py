# Temperature control class, responsible for activating the heater and send alert when humidity goes out of range

class TempControl:

	def __init__(self, h_ref):

		self.t_ref = None
		self.h_ref = h_ref
		self.light = None

	def setReferenceTemperature(self, t_ref):										# SET THE REFERENCE TEMPERATURE

		if (t_ref == None):
			self.t_ref = None
		else:
			self.t_ref = float(t_ref)

	def setCurrentLight(self, light):												# SET THE LIGHT STATUS TO IDENTIFY DAY/NIGHT
		
		self.light = str(light)

	def temp_control(self, temp):													# TEMPERATURE CONTROL

		if (self.t_ref == None or self.light == None):
			return None

		if (self.light == "1"):
			t_inf = self.t_ref - 1
			t_sup = self.t_ref + 1
		else:
			t_inf = self.t_ref - 5
			t_sup = self.t_ref - 3

		if (temp <= t_inf):
			return 1
		if (temp >= t_sup):
			return 0

		return None

	def hum_alert(self, hum):														# HUMIDITY ALERT

		h_inf = float(self.h_ref) - 6.0
		h_sup = float(self.h_ref) + 6.0

		if (hum <= h_inf or hum >= h_sup):
			return 1
		else:
			return 0