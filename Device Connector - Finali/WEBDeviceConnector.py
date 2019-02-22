#--------------- WEB DEVICE CONNECTOR---------------
#
# Structure:
#
# REST_DeviceConnector  <-- Implementation of all RESTful Services
#                           Using CherryPy
#
# MQTT_DeviceConnector  <-- Implementation of all Pub/Sub Services
#                           Using PahoMQTT
#
# THREADS               <-- Threads building section
#
# __main__              <-- All services are launched
#
#
# all info about the device in use are stored in 'config.txt' file


import requests
import cherrypy
import json
import os, os.path
import time
import paho.mqtt.client as PahoMQTT
import threading
import socket
from DeviceConnector import *



# RESTful Services 
#
# localhost:8080/temperature   <-- returns a SenMl related to Temperature
# localhost:8080/humidity      <-- returns a SenMl related to Humidity
# localhost:8080/lock_status   <-- returns a SenMl related to Lock Status
# localhost:8080/light_status  <-- returns a SenMl related to Ligth Status
# localhost:8080/photo         <-- returns a Photo



class REST_DeviceConnector:

    exposed = True

    def __init__(self, deviceconnector):
		
		self.deviceconnector = deviceconnector
			
		
    def GET (self, *uri):
                            
            if (uri[0] == 'temperature'):
                                        
                    senml = self.deviceconnector.temperature()
            
                    if senml is None:
                                    raise cherrypy.HTTPError(500, "Invalid Senml")
                                    
                    value = ((senml['e'])[0])['v'] 
                    
                    if isinstance(value, basestring):			
                            raise cherrypy.HTTPError(500, "Error in reading data from sensor")	
                    
                    else: 
                            out = json.dumps(senml)
            
            
            
            elif (uri [0] == 'humidity'):		
            
                    senml = self.deviceconnector.humidity()
            
                    if senml is None:
                            raise cherrypy.HTTPError(500, "Invalid Senml")

                            
                    value = ((senml['e'])[0])['v'] 
                    
                    
                    if isinstance(value, basestring):
                            raise cherrypy.HTTPError(500, "Error in reading data from sensor")
                            
                    else: 
                            out = json.dumps(senml)
    
    
    
            elif (uri [0] == 'lock_status'):
                    
                    senml = self.deviceconnector.lock_status()
            
                    
                    if senml is None:
                            raise cherrypy.HTTPError(500, "Invalid Senml")
                            
                    else: 
                            out = json.dumps(senml)
                            
                            
                    
            elif (uri [0] == 'light_status'):
                    
                    senml = self.deviceconnector.light_status()
            
                    
                    if senml is None:			
                            raise cherrypy.HTTPError(500, "Invalid Senml")
                            
                    else: 
                            out = json.dumps(senml)

                                            
                                            
            elif (uri [0] == 'photo'):
                    out = """<html>
                    <head>
                    </head>
                    <body>
                        <img src = "/static/image1.jpeg" />
                    </body>
                    </html>
                    
                    """
            return out	
			


			
# Pub/Sub Services
#
# Device Connector is Publisher for these topics:
#
# Pub --> /SPYthon/nagini/temperature
# Pub --> /SPYthon/nagini/humidity
# Pub --> /SPYthon/nagini/light_status
# Pub --> /SPYthon/nagini/lock_status
#
# Device Connector is Subscriber for these topics:
#
# Sub <-- /SPYthon/nagini/Tcontrol
# Sub <-- /SPYthon/nagini/Lcontrol
# Sub <-- /SPYthon/nagini/Halert
#
# where 'nagini' in this case is my DeviceID
# all info about the device are in 'config.txt' file



class MQTT_DeviceConnector:

	def __init__(self, clientID, deviceID, broker, port,deviceconnector):
                self.deviceconnector=deviceconnector
		self.broker = broker
		self.port = port
		self.clientID = clientID
		self.deviceID = deviceID
		self._topic = ""                
		self._isSubscriber = False
		
		# create an instance of paho.mqtt.client
		self._paho_mqtt = PahoMQTT.Client(clientID, False)

		# register the callback
		self._paho_mqtt.on_connect = self.myOnConnect
		self._paho_mqtt.on_message = self.myOnMessageReceived
			
	def myOnConnect (self, paho_mqtt, userdata, flags, rc):
		print ("Connected to %s with result code: %d" % (self.broker, rc))

	def myOnMessageReceived (self, paho_mqtt , userdata, msg):
	    
	    #print msg.topic
	    #print msg.payload
	    
	    msg_dict = json.loads(str(msg.payload))

            if (msg.topic == '/SPYthon/'+ self.deviceID +"/Tcontrol"):
                            
                control = msg_dict['v']
                
                self.deviceconnector.Tcontrol(int(control))
            
            elif (msg.topic =='/SPYthon/'+ self.deviceID +"/Lcontrol"):
                
                control = msg_dict['v']
               
                self.deviceconnector.Lcontrol(control)
                    
            elif (msg.topic == '/SPYthon/'+ self.deviceID +"/Halert"):
                
                alert = msg_dict['v']
                
                self.deviceconnector.Halert(alert)
                


	def myPublish (self, topic, msg):
	
		#print ("publishing '%s' with topic '%s'" % (msg, topic))
		# publish a message with a certain topic
		self._paho_mqtt.publish(topic, json.dumps(msg) , 2)

	def mySubscribe (self, topic):
		# if needed, you can do some computation or error-check before subscribing
		print ("subscribing to %s" % (topic))
		# subscribe for a topic
		self._paho_mqtt.subscribe(topic, 2)
		# just to remember that it works also as a subscriber
		self._isSubscriber = True
		self._topic = topic

	def start(self):
		#manage connection to broker
		self._paho_mqtt.connect(self.broker , self.port)
		self._paho_mqtt.loop_start()

	def stop (self):
		if (self._isSubscriber):
			# remember to unsuscribe if it is working also as subscriber
			self._paho_mqtt.unsubscribe(self._topic)
		self._paho_mqtt.loop_stop()
		self._paho_mqtt.disconnect()

		
		

# THREADS
#
# Used by Device Connector to publish and register itself
#
# Publishes Temperature each 15 seconds 
# Publishes Humidity each 30 seconds 
# Publishes Light Status each 45 seconds 
# Publishes Lock Status each 60 seconds 
#
# Register itself each 5 minutes

		
class Registration(threading.Thread):  
	def __init__(self,deviceconnector, conf_file_dict):
	
		threading.Thread.__init__(self)
		
		self.conf_file_dict=conf_file_dict
		
        
 	def run(self):
 		while True:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(("8.8.8.8", 80))
			ip = s.getsockname()[0]
			
			myport=8080
			catalogIP = self.conf_file_dict['catalogIP']
			deviceID = self.conf_file_dict['deviceID']
			psw = self.conf_file_dict['psw']

			initstring = "/SPYthon/" + deviceID
	
			#DEVICE registration  
			get = ["temperature", "humidity", "lock_status","light_status", "photo"]    
			sub_topics = [initstring + "/Tcontrol", initstring + "/Lcontrol",initstring + "/Halert"]
			pub_topics = [initstring + "/temperature", initstring + "/humidity", initstring + "/light_status", initstring + "/lock_status"]
			resources = ["temperature", "humidity", "lock_status","light_status", "photo", "Tcontrol", "Lcontrol"]
	
			payload = {'ID': deviceID, 'IP': ip ,'psw' : psw , 'port':myport, 'GET': get , 'POST' : [] , 'sub_topics':sub_topics, 'pub_topics': pub_topics, 'resources': resources}
	
			try:
				r1 = requests.post('http://'+ catalogIP + ':8080/add_device/terrarium' , data = json.dumps(payload)  )
				r1.raise_for_status()
				
				r2 = requests.get('http://'+ catalogIP + ':8080/broker')
				r2.raise_for_status()

				brokerip = r2.json()['broker_IP']
				brokerport = r2.json()['broker_port']

			except requests.HTTPError as err:
					print 'Error in posting, aborting' 
					return
			
 			time.sleep(5*60)
 			

		
class Temp(threading.Thread):  
	def __init__(self,pub,deviceconnector, deviceID):
		threading.Thread.__init__(self)
                self.pub = pub
		self.deviceconnector=deviceconnector
		self.deviceID=deviceID
 	def run(self):
 		while True:
                        senml_temp = self.deviceconnector.temperature()
                        
			self.pub.myPublish('/SPYthon/'+ self.deviceID + '/temperature', json.dumps(senml_temp))
 			time.sleep(15)



class Hum(threading.Thread):
 	def __init__(self,pub, deviceconnector, deviceID):
		threading.Thread.__init__(self)
                self.pub = pub
		self.deviceconnector=deviceconnector
		self.deviceID= deviceID
 	def run(self):
 		while True:
                        senml_hum = self.deviceconnector.humidity()
                    
			self.pub.myPublish('/SPYthon/'+ self.deviceID +'/humidity', json.dumps(senml_hum))
 			time.sleep(30)


		
class Light(threading.Thread):
	def __init__(self,pub,deviceconnector,deviceID):
		threading.Thread.__init__(self)
                self.pub = pub
		self.deviceconnector=deviceconnector
		self.deviceID= deviceID
     
	def run(self):
		while True: 
                        light = self.deviceconnector.light_status()
			self.pub.myPublish('/SPYthon/'+ self.deviceID +'/light_status', json.dumps(light))
                        time.sleep(45)


			
class Lock(threading.Thread):
 	def __init__(self,pub,deviceconnector,deviceID):
 		threading.Thread.__init__(self)
                self.pub = pub
		self.deviceconnector=deviceconnector
		self.deviceID= deviceID
 	def run(self):
 		while True:
                        lockStatus = self.deviceconnector.lock_status()
			self.pub.myPublish('/SPYthon/'+ self.deviceID +'/lock_status', json.dumps(lockStatus))
 			time.sleep(60)

			
			
if __name__ == "__main__":

        # Needed to register the first time WebDeviceConnector is run
        
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	ip = s.getsockname()[0]
	
	myport= 8080
	deviceconnector = DeviceConnector(ip) 

	conf_file = open("config.txt", 'r')
	conf_file_dict = json.loads(conf_file.read())
	conf_file.close()

	catalogIP = conf_file_dict['catalogIP']
	deviceID = conf_file_dict['deviceID']
	psw = conf_file_dict['psw'] 

	initstring = "/SPYthon/" + deviceID
	
	#DEVICE registration  
	get = ["temperature", "humidity", "lock_status","light_status", "photo"]    
	sub_topics = [initstring + "/Tcontrol", initstring + "/Lcontrol",initstring + "/Halert"]
	pub_topics = [initstring + "/temperature", initstring + "/humidity", initstring + "/light_status", initstring + "/lock_status"]
	resources = ["temperature", "humidity", "lock_status","light_status", "photo", "Tcontrol", "Lcontrol"]
	
	payload = {'ID': deviceID, 'IP': ip , 'psw': psw, 'port': myport, 'GET': get , 'POST' : [] , 'sub_topics':sub_topics, 'pub_topics': pub_topics, 'resources': resources}
	
	try:
		r1 = requests.post('http://'+ catalogIP + ':8080/add_device/terrarium' , data = json.dumps(payload)  )
		r1.raise_for_status()
		
		r2 = requests.get('http://'+ catalogIP + ':8080/broker')
		r2.raise_for_status()

		brokerip = r2.json()['broker_IP']
		print brokerip
		brokerport = r2.json()['broker_port']

	except requests.HTTPError as err:
            print 'Error in posting, aborting' 
            sys.exit()
		
	
	# CherryPy 
	
	conf = {
	    '/': {
	    'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': '.'
        }
    }

		

	# MQTT services and Threads
		
	test = MQTT_DeviceConnector('MQTT_DeviceConnector', deviceID, brokerip, brokerport, deviceconnector)
	
		
	Registration = Registration(deviceconnector,conf_file_dict)	
	Temperature= Temp(test,deviceconnector,deviceID)
	Humidity = Hum(test,deviceconnector,deviceID)
	Light_status = Light(test,deviceconnector,deviceID)
        Lock_status = Lock(test,deviceconnector,deviceID)
	
	
	test.start()

	
	test.mySubscribe(initstring + '/Tcontrol')
        test.mySubscribe(initstring + '/Lcontrol')
	test.mySubscribe(initstring + '/Halert')
	
	
	Registration.start()
	Temperature.start()
	Humidity.start()
	Light_status.start()
	Lock_status.start()
	
	
	# RESTful services 
	
	cherrypy.tree.mount(REST_DeviceConnector(deviceconnector) , '/', conf)
	cherrypy.config.update({'server.socket_host': '0.0.0.0'})
	cherrypy.config.update({'server.socket_port': 8080})
	cherrypy.engine.start()
	cherrypy.engine.block()
		
		




















	
	


# SPYthon - Domenico Minervini 2019	


