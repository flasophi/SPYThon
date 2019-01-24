# The Control is accessible through REST web services.
# Control strategies are implemented in the class Control(), defining lower and upper limit for temperature and humidity,
# and a check for consistency of the light status. The user shall define the reference temperature and the reference humidity,
# while the bounds are defined. The user shall also define the starting and stop time for illumination (dawn and dusk).
#
# - (temp)GET:		- /temperature?temp=<temp>				-> set temperature parameter
#
# - (light)GET:		- /light?dawn=<hh:mm>&dusk=<hh:mm>		-> set illumination parameters
#
# - MQTT_sub		- SPYthon/ + deviceID + /temperature	-> temperature value	(INT)
#					- SPYthon/ + deviceID + /humidity		-> humidity value		(INT)
#					- SPYthon/ + deviceID + /light_status	-> light status			"ON"/"FF"
#
# - MQTT_pub		- SPYthon/ + deviceID + /Tcontrol		-> heater command		0/1
#					- SPYthon/ + deviceID + /Lcontrol		-> light instruction	{"light command":0/1,"light alert":0/1}
#					- SPYthon/ + deviceID + /Halert			-> humidity alert		0/1
#
# corrections at column 105

import cherrypy
import requests
import json
import socket
import threading
import time
import sys
from TempControl import *
from LightControl import *
	
			#	RAISE EXCEPTIONS, ARSEHOLE
			
class WebTemp:																		# REST CORRESPONDENT TO TEMPERATURE CONTROL
	
	def __init__(self, controller):
	
		self.controller = controller
	
	def GET(self,*uri,**params):

		try:
			t_ref = params["temp"]
			self.controller.t_ref_setting(t_ref)
		except:
			raise cherrypy.HTTPError(400,"need proper format")

class WebLight:																		# REST CORRESPONDENT TO LIGHT CONTROL

	def __init__(self, controller):
	
		self.controller = controller
	
	def GET(self,*uri,**params):

		try:
			ref_dawn = params["dawn"]
			ref_dusk = params["dusk"]
			self.controller.l_ref_setting(dawn,dusk)
		except:
			raise cherrypy.HTTPError(400,"need proper format")

class MQTTControl():
	
	def __init__(self, deviceID, controller, brokerip, brokerport):

		try:
			self.broker = brokerip
			self.port = brokerport
		except:
			raise "no broker registered"																# check the correct format for the error, here
		
		self.controller = controller
		self.deviceID = deviceID
		self.topic = ""
		self.input = ""
		self.flag = 0
		
		# create an instance of paho.mqtt.client
		self._paho_mqtt = PahoMQTT.Client(deviceID, False) 

		# register the callback
		self._paho_mqtt.on_connect = self.myOnConnect
		self._paho_mqtt.on_message = self.myOnMessage
		
	def myOnConnect(self, paho_mqtt, userdata, flags, rc):
	
		print ("Connected to %s with result code: %d" % (self.broker, rc))
		
	def myOnMessage(self, paho_mqtt, userdata, msg):

		# A new message is received
		print ("Topic:'" + msg.topic + "', QoS: '" + str(msg.qos) + "' Message: '" + str(msg.payload) + "'")
		self.flag = 1
		self.topic = msg.topic
		self.input = msg.payload
		
	def start(self):

		self._paho_mqtt.connect(self.broker, self.port)
		self._paho_mqtt.loop_start()
		
	def stop(self):
	
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()

	def subscribe(self, topic):

		self._paho_mqtt.subscribe(topic, 2)
		
	def publish(self, topic, message):

		self._paho_mqtt.publish(topic, message, 2)
		self.flag = 0

class MQTTThread(threading.Thread):
	
	def __init__(self, threadID, topic, actor):
		
		self.actor = actor
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.topic = topic
		self.output = ""
		self.message = ""
		self.input = ""
		self.flag = 1
		
	def control_choice(self, deviceID):
		
		if("temperature" in self.topic):
			actor.t_setting(self.input)
			self.output = "SPYthon/" + deviceID + "/Tcontrol"
			
			if (actor.controller.temp_control() == None):
				self.flag = 0																			# check if the flag is needed or if it's sufficient to have the value "None"
			else:
				self.flag = 1
				
			return actor.controller.temp_control()
			
		elif("light_status" in self.topic):
			actor.l_setting(self.input)
			self.output = "SPYthon/" + deviceID + "/Lcontrol"
						
			if (actor.controller.light_control() == None):
				self.flag = 0																			# check if the flag is needed or if it's sufficient to have the value "None"
			else:
				self.flag = 1
				
			return actor.controller.light_control()														# add light_alert
			
		elif("humidity" in self.topic):
			actor.h_setting(self.input)
			self.output = "SPYthon/" + deviceID + "/Halert"
			return actor.controller.hum_alert()
	
	def update(self):
		
		self.input = self.actor.input						# input from the topic to which is subscribed
	
	def run(self):
		
		while True:
			deviceID = self.actor.deviceID
			self.update()									# update the input
			self.message = self.control_choice(deviceID)	# select the correct control
			self.action()									# publish
		
	def action(self):

		if (actor.flag == 1 and self.flag == 1):			# if there's an input AND if the control is active
			actor.publish(self.output,self.message)														# evaluate if adding an "else" might help the debug

class TempRegistration(threading.Thread): 
 
	def __init__(self, controller, deviceID, catalogip):
	
		threading.Thread.__init__(self)
		self.controller = controller
		self.deviceID = deviceID
		self.catalogip = catalogip
		self.controllerip = string(socket.gethostbyname(socket.gethostname())) + ":8080/"
        
 	def run(self):
 		
		while True:	
				# impose url to add temperature control and humidity alert
			
			url = "http://" + self.catalogip + ":8080/add_device/tempcontrol"							# better specify port on the config file?
			
				# bodies of the post
			
			tempID = ["tempcontrol"]
			tempGET = ["temperature?temp=<temp>"]
			tempsub = ["SPYthon/" + self.deviceID + "/temperature", "SPYthon/" + self.deviceID + "/humidity"]
			temppub = ["SPYthon/" + self.deviceID + "/Tcontrol", "SPYthon/" + self.deviceID + "/Halert"]
			
			data = {"ID":tempID,"IP":self.controllerip,"GET":tempGET,"POST":[],"sub_topics":tempsub,"pub_topics":temppub,
					"temp":self.controller.temp_read,"terrarium":self.deviceID}
			
				# requests.post
			
			try:
				r = requests.post(url, data=json.dumps(data))
				r.raise_for_status()
				
			except request.HTTPError as err:
				print "Error in posting, aborting"
				return
			
			time.sleep(15*60)

class LightRegistration(threading.Thread):
	
	def __init__(self, controller, deviceID, catalogip):
	
		threading.Thread.__init__(self)
		self.controller = controller
		self.deviceID = deviceID
		self.catalogip = catalogip
		self.controllerip = string(socket.gethostbyname(socket.gethostname())) + ":8080/"
        
 	def run(self):
 		
		while True:	
				# impose url to add light control
			
			url = "http://" + self.catalogip + ":8080/add_device/lightcontrol"							# better specify port on the config file?
			
				# body of the post
			
			lightID = ["lightcontrol"]
			lightGET = ["light?dawn=<hh:mm>&dusk=<hh:mm>"]
			lightsub = ["SPYthon/" + self.deviceID + "/light_status"]
			lightpub = ["SPYthon/" + self.deviceID + "/Lcontrol"]
			
			data = {"ID":lightID,"IP":self.controllerip,"GET":lightGET,"POST":[],"sub_topics":lightsub,"pub_topics":lightpub,
					"dawn":self.controller.dawn_read,"dusk":self.controller.dusk_read,"terrarium":self.deviceID}
			
				# requests.post
			
			try:
				r = requests.post(url, data=json.dumps(data))
				r.raise_for_status()
				
			except request.HTTPError as err:
				print "Error in posting, aborting"
				return
			
			time.sleep(15*60)
# MAIN

if __name__ == '__main__':
	
	file = open("config.txt","r")
	data = json.loads(file.read())
	catalogip = data["catalogip"]
	deviceID = data["deviceID"]
	file.close()
	
	try:
		broker = requests.get("http://" + catalogip + ":8080/broker")									# better specify port on the config file?
		broker.raise_for_status()
		brokerip = broker["broker_IP"]
		brokerport = broker["broker_port"]
	except requests.HTTPError as err:
		print "Error retrieving the broker"
		sys.exit()
	
	Charmender = TempControl()
	Pikachu = LightControl()
	
	TempActor = MQTTControl(deviceID, Charmender, brokerip, brokerport)
	LightActor = MQTTControl(ddeviceID, Pikachu, brokerip, brokerport)
	
	temp_registration = TempRegistration(Charmender, deviceID, catalogIP)
	light_registration = LightRegistration(Pikachu, deviceID, catalogIP)
	
	conf = {
		'/': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.sessions.on': True
		}
	}
	cherrypy.tree.mount(WebTemp(Charmender), '/temperature', conf)
	cherrypy.tree.mount(WebLight(Pikachu), '/light', conf)
	cherrypy.config.update({'server.socket_host': '0.0.0.0'})
	cherrypy.config.update({'server.socket_port': 8080})
	cherrypy.engine.start()
	cherrypy.engine.block()
	
	thread_temp = MQTTThread(1, "SPYthon/" + deviceID + "/temperature", TempActor)
	thread_hum = MQTTThread(3, "SPYthon/" + deviceID + "/humidity", TempActor)
	thread_light = MQTTThread(2, "SPYthon/" + deviceID + "/light_status", LightActor)
	
	TempActor.start()
	TempActor.subscribe("SPYthon/" + deviceID + "/temperature")
	TempActor.subscribe("SPYthon/" + deviceID + "/humidity")
	LightActor.subscribe("SPYthon/" + deviceID + "/light_status")
	
	temp_registration.start()
	light_registration.start()
	thread_temp.start()
	thread_light.start()
	thread_hum.start()
