#---------------DEVICE CONNECTOR---------------
#
# SENSORS:
#
# temperature   <-- read by DHT22 
# humidity      <-- read by DHT22
# lock_status   <-- emulated by using wire
# light_status  <-- emulated by using wire
# photo         <-- emulated by storing image on the RPi
#
# ACTUATORS:
#
# Tcontrol      <-- controls pin associated to Relay of Heating System
# Lcontrol      <-- controls PlugWise Smart Plug
#


import json
import RPi.GPIO as GPIO
import time
import Adafruit_DHT
from plugwise import *


class DeviceConnector:
			
	def __init__(self,ip):

	
		# IP 
		self.ip = ip
		
		# LOCK PIN
		self.pin_lock=26
		
		# LIGHT PIN (emulated with wire)
		self.pin_light=5
		
		# DHT22 (T & H sensor)
		self.pin_dht=18
		self.dht_sensor=Adafruit_DHT.DHT22   							  
		
		# GPIO
		GPIO.setmode(GPIO.BCM)  
		self.pin_rele1 = 12 #For heating relay
		
		# SMART PLUG
		self.mac1 = "000D6F0005670E36"
		self.mac2 = "000D6F0004B1E48D"
		self.usbport = "/dev/ttyUSB0"   # in up-right usb port 
		
		# ALERT
		self.humidityalert = 0 #alert off
		
		
		# CAMERA
		self.image_path= "/home/pi/Pictures/image1.jpeg"
		
	
		
		
		
	def temperature (self):

                # Retrieves Temperature value from sensor DHT22 and gives back a SenMl as output
	
		humidity, temperature = Adafruit_DHT.read_retry(self.dht_sensor, self.pin_dht)
		
		if temperature is not None:
		
			T_senml = {"bn": "http://" + self.ip + "/Tsensor/", "e": [{ "n": "temperature", "u": "Celsius","t": time.time(), "v": temperature}]}
		else:	
			T_senml = {"bn": "http://" + self.ip + "/Tsensor/", "e": [{ "n": "temperature", "u": "Celsius","t": time.time(), "v": "Error in reading"}]}
		
		#print T_senml
		print "Temperature is: " + str(((T_senml['e'])[0])['v'] ) + " Celsius" 
		return T_senml

	
	
	def humidity (self):

                # Retrieves Humidity value from sensor DHT22 and gives back a SenMl as output

	
		humidity, temperature = Adafruit_DHT.read_retry(self.dht_sensor, self.pin_dht)
		
		if humidity is not None:
		
			H_senml= {"bn": "http://" + self.ip + "/Hsensor/", "e": [{ "n": "humidity", "u": "%","t": time.time(), "v": humidity} , { "n": "alert", "u": "none","t": time.time(), "v": self.humidityalert}]}
		else:	
			H_senml= {"bn": "http://" + self.ip + "/Hsensor/", "e": [{ "n": "humidity", "u": "%","t": time.time(), "v": "Error in reading"},  { "n": "alert", "u": "none","t": time.time(), "v": self.humidityalert}]}
		
		#print H_senml
		print "Humidity is: " + str(((H_senml['e'])[0])['v'] )+ " %" 
		return H_senml
	
	

	def lock_status(self):

                # Retrieves Lock Status from reading proper GPIO PIN and gives back a SenMl as output


		GPIO.setup(self.pin_lock, GPIO.IN, GPIO.PUD_DOWN)
	
		if GPIO.input(self.pin_lock) == True :
		
			Lock_senml= {"bn": "http://" + self.ip + "/Lock_sensor/", "e": [{ "n": "lock_status", "u": "state","t": time.time(), "v": "closed"}]}
		else:	
			Lock_senml= {"bn": "http://" + self.ip + "/Lock_sensor/", "e": [{ "n": "lock_status", "u": "state","t": time.time(), "v": "open"}]}
		
		GPIO.cleanup(self.pin_lock)
		
		#print Lock_senml
		print "Lock status is: " + ((Lock_senml['e'])[0])['v'] 
		return Lock_senml
	
	
		
	def light_status(self):

                # Retrieves Light Status from reading proper GPIO PIN and gives back a SenMl as output

                
                GPIO.setup(self.pin_light, GPIO.IN, GPIO.PUD_DOWN)

		if GPIO.input(self.pin_light) == True :
		
			Light_senml= {"bn": "http://" + self.ip + "/Light_sensor/", "e": [{ "n": "light_status", "u": "state","t": time.time(), "v": 1}]}
		else:	
			Light_senml= {"bn": "http://" + self.ip + "/Light_sensor/", "e": [{ "n": "light_status", "u": "state","t": time.time(), "v": 0}]}
		
		GPIO.cleanup(self.pin_light)
		
		#print Light_senml
		print "Light status is: " + str(((Light_senml['e'])[0])['v'] )
		return Light_senml
	

	    
	def photo(self):
                
                # Retrieve Photo from RaspberryPi Camera and stores in a proper path

                
                # EMULATED 
                
		pass



	def Tcontrol(self, control):

                # Receives 1  or  0 to set HIGH or LOW the pin related to Heating System Relay
                
                # Implemented using the GPIO
				
		GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                GPIO.setup(self.pin_rele1,GPIO.OUT)
		
		
		if int(control) == 1 :
			
			GPIO.output(self.pin_rele1, GPIO.HIGH)
		else:
                    	GPIO.output(self.pin_rele1, GPIO.LOW)

						
		
	def Lcontrol(self, control):

                # Receives 1  or  0 to set ON or OFF the Smart Plug receiver

                # Implemented using PlugWise SmartPlug
                # following two lines are provided on Datasheet 
		
		s = Stick(port=self.usbport)
	
		c1,c2 = Circle(self.mac1,s) , Circle(self.mac2,s) 
		
	    
		if int(control) == 1 :
			
			c1.switch_on()	
		else: 
			c1.switch_off()

			
			
	def Halert (self, alert):

                # Stores the value of humidity alert
		
		 self.humidityalert = alert
		
		 








		 
		 
	
 # SPYthon - Domenico Minervini 2019

