# The Light Control is accessible through REST web services.
# Control strategies are implemented in the class LightControl(), activting the light of the terrarium.
# The user shall define the starting and stop time for illumination (dawn and dusk).
#
# - GET:			- /light?dawn=<hh:mm>&dusk=<hh:mm>		-> set illumination parameters
#
# - MQTT_pub:		- /SPYthon/ + deviceID + /Lcontrol		-> light instruction	{"v":0/1}

import cherrypy
import requests
import json
import socket
import threading
import time
import sys
import paho.mqtt.client as PahoMQTT
from TempControl import *
from LightControl import *

			
class WebLight:																		# REST CORRESPONDENT TO LIGHT CONTROL
	
	exposed = True
	
	def __init__(self, controller):
	
		self.controller = controller
	
	def GET(self,*uri,**params):

		if (len(uri) > 0 and len(params)>0):

			if (uri[0] == "light"):
				try:
					ref_dawn = params["dawn"]
					ref_dusk = params["dusk"]
					self.controller.l_ref_setting(ref_dawn,ref_dusk)
					print "set references from dusk till dawn"
				except:
					raise cherrypy.HTTPError(400,"need proper format")
					print "error in parameters content"
			else:
				raise cherrypy.HTTPError(400,"format error in uri")
				print "error in uri content"
		else:
			raise cherrypy.HTTPError(400,"need proper format in uri")
			print "error in data structure"

		return "all good in the jungle"
			
class MQTTControl():																# MQTT CLASS
	
	def __init__(self, deviceID, terrariumID, controller, brokerip, brokerport):

		try:
			self.broker = brokerip
			self.port = brokerport
		except:
			raise "no broker registered"
		
		self.controller = controller
		self.terrariumID = terrariumID
		self.topic = ""
		self._paho_mqtt = PahoMQTT.Client(deviceID, False) 
		self._paho_mqtt.on_connect = self.myOnConnect
		
	def myOnConnect(self, paho_mqtt, userdata, flags, rc):
	
		print ("Connected to %s with result code: %d" % (self.messageBroker, rc))
		
	def start(self):

		self._paho_mqtt.connect(self.broker, self.port)
		self._paho_mqtt.loop_start()
		
	def stop(self):
	
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()
		
	def publish(self, topic, message):
		self._paho_mqtt.publish(topic, message, 2)
		
class LightThread(threading.Thread):												# LIGHT CONTROL THREAD

	def __init__(self, threadID, actor, controller):
		
		self.actor = actor
		self.controller = controller
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.topic = "/SPYthon/" + self.actor.terrariumID + "/Lcontrol"
	
	def run(self):
	
		while True:
			command = self.controller.light_control()
			if (command != None):
				message = json.dumps({"v":command})
				self.actor.publish(self.topic,message)
			time.sleep(1)

class LightRegistration(threading.Thread):											# LIGHT REGISTRATION TO THE CATALOG THREAD
	
	def __init__(self, controller, deviceID, terrariumID, catalogurl):
	
		threading.Thread.__init__(self)
		self.controller = controller
		self.terrariumID = terrariumID
		self.deviceID = deviceID
		self.catalogurl = catalogurl
        
 	def run(self):
 		
		while True:	

			url = self.catalogurl + "add_device/lightcontrol"
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(("8.8.8.8",80))
			controllerip = s.getsockname()[0]
			lightGET = ["light?dawn=<hh:mm>&dusk=<hh:mm>"]
			lightpub = ["/SPYthon/" + self.terrariumID + "/Lcontrol"]
			
			data = {"ID":deviceID,"IP":controllerip,"port":9090,"GET":lightGET,"POST":[],"sub_topics":[],"pub_topics":lightpub,
					"dawn":str(self.controller.dawn_read),"dusk":str(self.controller.dusk_read),"terrarium":self.terrariumID}
					
			try:
				r = requests.post(url, data=json.dumps(data))
				r.raise_for_status()
				
			except requests.HTTPError as err:
				print "Error in posting, aborting"
				return
			
			time.sleep(15*60)


if __name__ == '__main__':															# MAIN
	
	file = open("configControl.txt","r")
	data = json.loads(file.read())
	catalogip = data["catalogip"]
	catalogport = data["catalogport"]
	deviceID = "LightControl"
	terrariumID = data["terrariumID"]
	file.close()
	catalogurl = "http://" + catalogip + catalogport
	
	try:
		r = requests.get(catalogurl + "broker")
		r.raise_for_status()
		broker = r.json()
		brokerip = broker["broker_IP"]
		brokerport = broker["broker_port"]
	except requests.HTTPError as err:
		print "Error retrieving the broker"
		sys.exit()
	
	Pikachu = LightControl()
	
	LightActor = MQTTControl(deviceID, terrariumID, Pikachu, brokerip, brokerport)
	
	light_registration = LightRegistration(Pikachu, deviceID, terrariumID, catalogurl)
	
	thread_light = LightThread(1, LightActor, Pikachu)
	
	LightActor.start()
	
	light_registration.start()
	thread_light.start()
	
	conf = {
		'/': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.sessions.on': True
		}
	}
	cherrypy.tree.mount(WebLight(Pikachu), '/', conf)
	cherrypy.config.update({'server.socket_host': '0.0.0.0'})
	cherrypy.config.update({'server.socket_port': 9090})
	cherrypy.engine.start()
	cherrypy.engine.block()