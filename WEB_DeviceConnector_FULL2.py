import requests
import cherrypy
import json
import os, os.path
import time

import paho.mqtt.client as PahoMQTT

import threading

import socket

from DeviceConnector import *

import threading

#POSSIBILITIES   REST-ful
# localhost:8080/temperature
# localhost:8080/humidity      <-- oltre a mandare hum, ti informo con {h:val, alert:boolean}
# localhost:8080/lock_status   
# localhost:8080/light_status  <-- fake 
# localhost:8080/photo         <-- fake (3 foto)




# RICORDA : fai la init dove comunichi al caltalogue il mio ip
# id_device :"ID", IP,GET [temperature, humidity, loc,..], POST [],lista topic [] 
 
 #DA fare: 1 solo device connector per MQTT e RESTFUL
 
 





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
			
			
			# Pub-Sub	
	
# Pub --> brokerip/temp
# Pub --> brokerip/hum
# Pub --> brokerip/light

# Sub ..> brokerip/Tcontrol
# Sub ..> brokerip/Lcontrol
# Sub ..> brokerip/Halert




class MQTT_DeviceConnector:

	def __init__(self, clientID, deviceID, broker, port,deviceconnector):
                self.deviceconnector=deviceconnector
		self.broker = broker
		self.port = port
		self.clientID = clientID
		self.deviceID = deviceID
		self._topic = ""                #chiedi
		self._isSubscriber = False      #chiedi
		# create an instance of paho.mqtt.client
		self._paho_mqtt = PahoMQTT.Client(clientID, False)

		# register the callback
		self._paho_mqtt.on_connect = self.myOnConnect
		self._paho_mqtt.on_message = self.myOnMessageReceived


		#list of topics for sub and pub
		
		#self.sub_topics= [initstring + "/Tcontrol", initstring + "/Lcontrol",initstring + "/Halert"]
		#self.pub_topics= [initstring + "/temperature", initstring + "/humidity", initstring + "/light_status", initstring + "/lock_status"]
			
	def myOnConnect (self, paho_mqtt, userdata, flags, rc):
		print ("Connected to %s with result code: %d" % (self.broker, rc))

	def myOnMessageReceived (self, paho_mqtt , userdata, msg):
		# A new message is received 
	    print (msg.topic, msg.payload)
	    print msg.topic
	    print msg.payload
	    print "-"
	    print "-"
		
        #payload deve essere un senml, nel campo "v" c' il
        #valore atteso (1 acceso, 0 spento)
	    
	    
	    msg_dict = json.loads(str(msg.payload))
        # mi arriva il json con il controllo se 1 o 0
            if (msg.topic == 'SPYthon/'+ self.deviceID +"/Tcontrol"):
                            
                control = ((msg_dict['e'])[0])['v']
                
                self.deviceconnector.Tcontrol(int(control))
            
            elif (msg.topic =='SPYthon/'+ self.deviceID +"/Lcontrol"):
                control = ((msg_dict['e'])[0])['v']
               
                self.deviceconnector.Lcontrol(control)
                    
            elif (msg.topic == 'SPYthon/'+ self.deviceID +"/Halert"):
                alert = msg_dict['v']
                print alert
                self.deviceconnector.Halert(alert)


	def myPublish (self, topic, msg):
	
		#print ("publishing '%s' with topic '%s'" % (msg, topic))
		# publish a message with a certain topic
		self._paho_mqtt.publish(topic, msg, 2)

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

		
		
	
### THREADS ###

		
		
class Registration(threading.Thread):  
	def __init__(self,deviceconnector, conf_file_dict):
	
		threading.Thread.__init__(self)
		
		self.conf_file_dict=conf_file_dict
		
        
 	def run(self):
 		while True:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(("8.8.8.8", 80))
			ip = s.getsockname()[0]
			
			
			catalogIP = self.conf_file_dict['catalogIP']
			deviceID = self.conf_file_dict['deviceID']

			initstring = "SPYthon/" + deviceID
	
			#DEVICE registration  
			get = ["temperature", "humidity", "lock_status","light_status", "photo"]    
			sub_topics = [initstring + "/Tcontrol", initstring + "/Lcontrol",initstring + "/Halert"]
			pub_topics = [initstring + "/temperature", initstring + "/humidity", initstring + "/light_status", initstring + "/lock_status"]
			resources = ["temperature", "humidity", "lock_status","light_status", "photo", "Tcontrol", "Lcontrol"]
	
			payload = {'ID': deviceID, 'IP': ip , 'GET': get , 'POST' : [] , 'sub_topics':sub_topics, 'pub_topics': pub_topics, 'resources': resources}
	
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
			self.pub.myPublish('SPYthon/'+ deviceID + '/temperature', json.dumps(senml_temp))
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
			self.pub.myPublish('SPYthon/'+ deviceID +'/humidity', json.dumps(senml_hum))
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
			self.pub.myPublish('SPYthon/'+ deviceID +'/light_status', json.dumps(light))
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
			self.pub.myPublish('SPYthon/'+ deviceID +'/lock_status', json.dumps(lockStatus))
 			time.sleep(60)

			
			
if __name__ == "__main__":

	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	ip = s.getsockname()[0]
	 
	deviceconnector = DeviceConnector(ip) 

	conf_file = open("config.txt", 'r')
	conf_file_dict = json.loads(conf_file.read())
	conf_file.close()

	catalogIP = conf_file_dict['catalogIP']
	deviceID = conf_file_dict['deviceID']

	initstring = "SPYthon/" + deviceID
	
	#DEVICE registration  
	get = ["temperature", "humidity", "lock_status","light_status", "photo"]    
	sub_topics = [initstring + "/Tcontrol", initstring + "/Lcontrol",initstring + "/Halert"]
	pub_topics = [initstring + "/temperature", initstring + "/humidity", initstring + "/light_status", initstring + "/lock_status"]
	resources = ["temperature", "humidity", "lock_status","light_status", "photo", "Tcontrol", "Lcontrol"]
	
	payload = {'ID': deviceID, 'IP': ip , 'GET': get , 'POST' : [] , 'sub_topics':sub_topics, 'pub_topics': pub_topics, 'resources': resources}
	
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
	cherrypy.tree.mount(REST_DeviceConnector(deviceconnector) , '/', conf)
	cherrypy.config.update({'server.socket_host': '0.0.0.0'})
	cherrypy.config.update({'server.socket_port': 8080})
	cherrypy.engine.start()
		
		
		
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
	
	
		
		
	# #qui come broker devo ottener l'ip del broker
	# test.start()

	# temp = Temp(test,deviceconnector)
	# hum = Hum(test,deviceconnector)
	# light_status = Light(test,deviceconnector)
    # lock_status = Lock(test,deviceconnector)


	# temp.start()
	# hum.start()
	# light_status.start()
	# lock_status.start()

	# test.mySubscribe(str(test.broker)+'/Tcontrol')
    # test.mySubscribe(str(test.broker)+'/Lcontrol')
	# test.mySubscribe(str(test.broker)+'/Halert')

	#while True:
	#	pass


	
	
	


