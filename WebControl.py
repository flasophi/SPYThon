# The Control is accessible through REST web services.
# Control strategies are implemented in the class Control(), defining lower and upper limit for temperature and humidity,
# and a check for consistency of the light status. The user shall define the reference temperature and the reference humidity,
# while the bounds are defined. The user shall also define the starting and stop time for illumination (dawn and dusk).
#
# - GET:		- /temperature?temp=<temp>				-> set temperature parameter
#				- /light?dawn=<hh:mm>&dusk=<hh:mm>		-> set illumination parameters
#
# - MQTT_sub	- SPYthon/ + deviceID + /temperature	-> temperature value
#				- SPYthon/ + deviceID + /humidity		-> humidity value
#				- SPYthon/ + deviceID + /light_status	-> light status (ON,OFF)
#
# - MQTT_pub	- SPYthon/ + deviceID + /Tcontrol		-> heater command
#				- SPYthon/ + deviceID + /Lcontrol		-> light command								# light alert?
#				- SPYthon/ + deviceID + /Halert			-> humidity alert
#
# corrections at column 105

import cherrypy
import request
import json
import socket
import threading
import time
from Control import *
	
			#	RAISE EXCEPTIONS, ARSEHOLE
			
class RESTControl:
	
	def __init__(self, controller):
	
		self.controller = controller
	
	def GET(self,*uri,**params):

		if(len(uri) == 0):
			raise cherrypy.HTTPError(400, "no command")
		else:
			try:
				if(uri[0] == "temperature"):
					t_ref = params["temp"]
					self.controller.t_ref_setting(t_ref)
			
				elif(uri[0] == "light"):
					ref_dawn = params["dawn"]
					ref_dusk = params["dusk"]
					self.controller.l_ref_setting(dawn,dusk)
			except:
				raise cherrypy.HTTPError(400,"need proper format")

class MQTTControl():
	
	def __init__(self, clientID, controller, broker):

		try:
			self.broker = broker
		except:
			raise "no broker registered"																# check the correct format for the error, here
		
		self.controller = controller
		self.clientID = clientID
		self.topic = ""
		self.input = ""
		self.flag = 0
		
		# create an instance of paho.mqtt.client
		self._paho_mqtt = PahoMQTT.Client(clientID, False) 

		# register the callback
		self._paho_mqtt.on_connect = self.myOnConnect
		self._paho_mqtt.on_message = self.myOnMessage
		
	def myOnConnect(self, paho_mqtt, userdata, flags, rc):
	
		print ("Connected to %s with result code: %d" % (self.messageBroker, rc))
		
	def myOnMessage(self, paho_mqtt, userdata, msg):

		# A new message is received
		print ("Topic:'" + msg.topic+"', QoS: '"+str(msg.qos)+"' Message: '"+str(msg.payload) + "'")
		self.flag = 1
		self.topic = msg.topic
		self.input = msg.payload
		
	def start(self):

		self._paho_mqtt.connect(self.broker, self.port)
		self._paho_mqtt.loop_start()
		
	def stop(self):
	
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()																	# doesn't need to know broker and port?

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
			deviceID = self.actor.controller.deviceID
			self.update()									# update the input
			self.message = self.control_choice(deviceID)	# select the correct control
			self.action()									# publish
		
	def action(self):

		if (actor.flag == 1 and self.flag == 1):			# if there's an input AND if the control is active
			actor.publish(self.output,self.message)														# evaluate if adding an "else" might help the debug

class Registration(threading.Thread): 
 
	def __init__(self, controller):
	
		threading.Thread.__init__(self)
		self.controller = controller
		self.controllerip = string(socket.gethostbyname(socket.gethostname())) + ":8080/"
        
 	def run(self):
 		
		while True:
			catalogip = self.controller.catalogip + ":8080/"											# better specify port on the config file?
			deviceID = self.controller.deviceID
	
				# impose url to add temperature control, light control and humidity alert
			
			light_url = "http://" + catalogip + ":8080/add_device/lightcontrol"							# better specify port on the config file?
			temp_url = "http://" + catalogip + ":8080/add_device/tempcontrol"							# better specify port on the config file?
			
				# bodies of the post
			
			tempID = ["tempcontrol"]
			tempGET = ["temperature?temp=<temp>"]
			tempsub = ["SPYthon/" + deviceID + "/temperature", "SPYthon/" + deviceID + "/humidity"]
			temppub = ["SPYthon/" + deviceID + "/Tcontrol", "SPYthon/" + device ID + "/Halert"]
			
			t_data = {"ID":tempID,"IP":self.controllerip,"GET":tempGET,"POST":[],"sub_topics":tempsub,"pub_topics":temppub,
					"temp":self.controller.temp_read,"terrarium":deviceID}
			
			lightID = ["lightcontrol"]
			lightGET = ["light?dawn=<hh:mm>&dusk=<hh:mm>"]
			lightsub = ["SPYthon/" + deviceID + "/light_status"]
			lightpub = ["SPYthon/" + deviceID + "/Lcontrol"]
			
			l_data = {"ID":lightID,"IP":self.controllerip,"GET":lightGET,"POST":[],"sub_topics":lightsub,"pub_topics":lightpub,
					"dawn":self.controller.dawn_read,"dusk":self.controller.dusk_read,"terrarium":deviceID}
			
				# requests.post
			
			try:
				r1 = requests.post(temp_url, data=json.dumps(t_data))
				r1.raise_for_status()
				
				r2 = requests.post(light_url, data=json.dumps(l_data))
				r2.raise_for_status()
				
			except request.HTTPError as err:
				print "Error in posting, aborting"
				return
			
			time.sleep(15*60)

# MAIN

if __name__ == '__main__':
	
	Big_Brother = Control()
	deviceID = Big_Brother.deviceID()
	
	try:
		broker = requests.get("http://" + catalogip + ":8080/broker")									# better specify port on the config file?
		broker.raise_for_status()
	except requests.HTTPError as err:
		print "Error retrieving the broker"
		return
		
	# actor_temperature = MQTTControl(Big_Brother, broker)
	# actor_light = MQTTControl(Big_Brother, broker)
	# actor_humidity = MQTTControl(Big_Brother, broker)
	actor = MQTTControl(Big_Brother, broker)
	
	conf = {
		'/': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.sessions.on': True
		}
	}
	cherrypy.tree.mount(WebControl(Big_Brother), '/', conf)
	cherrypy.config.update({'server.socket_host': '0.0.0.0'})
	cherrypy.config.update({'server.socket_port': 8080})
	cherrypy.engine.start()
	cherrypy.engine.block()
	
	registration = Registration(Big_Brother)
	thread_temp = MQTTThread(1, "SPYthon/" + deviceID + "/temperature", actor_temperature)
	thread_light = MQTTThread(2, "SPYthon/" + deviceID + "/light_status", actor_light)
	thread_hum = MQTTThread(3, "SPYthon/" + deviceID + "/humidity", actor_humidity)
	
	actor.start()
	actor.subscribe("SPYthon/" + deviceID + "/temperature")
	actor.subscribe("SPYthon/" + deviceID + "/light_status")
	actor.subscribe("SPYthon/" + deviceID + "/humidity")
	
	registration.start()
	thread_temp.start()
	thread_light.start()
	thread_hum.start()