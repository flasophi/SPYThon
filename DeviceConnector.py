import json
import RPi.GPIO as GPIO
import time
import Adafruit_DHT

import urllib #leggere ip

from plugwise import *

from StringIO import StringIO
from PIL import Image


#POSSIBILITIES   REST-ful
# localhost:8080/temperature
# localhost:8080/humidity      <-- oltre a mandare hum, ti informo con {h:val, alert:boolean}
# localhost:8080/lock_status   
# localhost:8080/light_status  <-- fake 
# localhost:8080/photo         <-- fake (3 foto)



# RICORDA : fai la init dove comunichi al caltalogue il mio ip
# id_device :"ID", IP,GET [temperature, humidity, loc,..], POST [],lista topic [] 


	

# Pub-Sub	
	
# Pub --> brokerip/temp
# Pub --> brokerip/hum

# Pub --> brokerip/light

# Sub ..> brokerip/Tcontrol
# Sub ..> brokerip/Lcontrol
# Sub ..> brokerip/Halert


class DeviceConnector:
			
	def __init__(self,ip):

	
		#IP READING
		#data = json.loads(urllib.urlopen("http://ip.jsontest.com/").read())
		#self.ext_ip = data["ip"]

		self.ip = ip
		
		#LOCK PIN
		self.pin_lock=26
		
		#LIGHT PIN (emulated with wire)
		self.pin_light=5
		
		#DHT22 (T & H sensor)
		self.pin_dht=18
		self.dht_sensor=Adafruit_DHT.DHT22   												#controlla bene 
		
		#GPIO
		GPIO.setmode(GPIO.BCM)  # the pin numbers refer to the board connector not the chip
		#GPIO.setup(self.pin_lock, GPIO.IN) # set up pin ?? (one of the above listed pins) as an input with a pull-up resistor
		GPIO.setup(self.pin_light, GPIO.IN) # set up pin ?? (one of the above listed pins) as an input with a pull-up resistor

		self.pin_rele1 = 12 #settalo bene
		
		#SMART PLUG
		self.mac1 = "000D6F0005670E36"
		self.mac2 = "000D6F0004B1E48D"
		self.usbport = "/dev/ttyUSB0"   # in alto a destra 
		
		#ALERT
		self.humidityalert = 0 #alert off
		
		
		#camera
		self.image_path= "/home/pi/Pictures/image1.jpeg"
		
	
		
		
		
	def temperature (self):  #vedi se nel senml posso cambiare formato da in caso di errore
	
		humidity, temperature = Adafruit_DHT.read_retry(self.dht_sensor, self.pin_dht)
		
		if temperature is not None:
		
			T_senml = {"bn": "http://" + self.ip + "/Tsensor/", "e": [{ "n": "temperature", "u": "Celsius","t": time.time(), "v": temperature}]}
		else:	
			T_senml = {"bn": "http://" + self.ip + "/Tsensor/", "e": [{ "n": "temperature", "u": "Celsius","t": time.time(), "v": "Error in reading"}]}
		
		print T_senml
		return T_senml
	
	def humidity (self):
	
		humidity, temperature = Adafruit_DHT.read_retry(self.dht_sensor, self.pin_dht)
		
		if humidity is not None:
		
			H_senml= {"bn": "http://" + self.ip + "/Hsensor/", "e": [{ "n": "humidity", "u": "%","t": time.time(), "v": humidity} , { "n": "alert", "u": "none","t": time.time(), "v": self.humidityalert}]}
		else:	
			H_senml= {"bn": "http://" + self.ip + "/Hsensor/", "e": [{ "n": "humidity", "u": "%","t": time.time(), "v": "Error in reading"},  { "n": "alert", "u": "none","t": time.time(), "v": self.humidityalert}]}
		
		print H_senml
		return H_senml

	def lock_status(self):
                #GPIO.setmode(GPIO.BCM)

               # GPIO.setmode(GPIO.BOARD)  # the pin numbers refer to the board connector not the chip
		GPIO.setup(self.pin_lock, GPIO.IN, GPIO.PUD_DOWN)
	
		if GPIO.input(self.pin_lock) == True :
		
			Lock_senml= {"bn": "http://" + self.ip + "/Lock_sensor/", "e": [{ "n": "lock_status", "u": "state","t": time.time(), "v": "closed"}]}
		else:	
			Lock_senml= {"bn": "http://" + self.ip + "/Lock_sensor/", "e": [{ "n": "lock_status", "u": "state","t": time.time(), "v": "open"}]}
		
		GPIO.cleanup(self.pin_lock)
		
		print Lock_senml
		return Lock_senml
		
	def light_status(self):
                
                GPIO.setup(self.pin_light, GPIO.IN, GPIO.PUD_DOWN)

		if GPIO.input(self.pin_light) == True :
		
			Light_senml= {"bn": "http://" + self.ip + "/Light_sensor/", "e": [{ "n": "light_status", "u": "state","t": time.time(), "v": 1}]}
		else:	
			Light_senml= {"bn": "http://" + self.ip + "/Light_sensor/", "e": [{ "n": "light_status", "u": "state","t": time.time(), "v": 0}]}
		
		GPIO.cleanup(self.pin_light)
		print Light_senml
		return Light_senml
	    
	def photo(self):
		pass
		#img = mpimg.imread(self.image_path)
		
	# conoscendo ip le prendi da raspberry
	# carico su sito online
	# mando link a cazzo 
	
	def Tcontrol(self, control):
		
		
		# Heater_senml = {'bn': self.ip + '/Heater_status/',
		#		'e': [{ "n": "Heater_status", "u": None,
		#		"t": time.time(), "v": 1}]}                  or 0
		
		GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                GPIO.setup(self.pin_rele1,GPIO.OUT)
		
		
		if int(control) == 1 :
			
			GPIO.output(self.pin_rele1, GPIO.HIGH)
			
			
		else:
                    			GPIO.output(self.pin_rele1, GPIO.LOW)

						
		
	def Lcontrol(self, control):
	
		# Lamp_senml = {'bn': self.ip + '/Lamp_status/',
		#		'e': [{ "n": "Lamp_status", "u": None,
		#		"t": time.time(), "v": 1}]}                  or 0
		
		#control = ((Lamp_senml['e'])[0])['v'] 
		
		s = Stick(port=self.usbport)
	
		c1,c2 = Circle(self.mac1,s) , Circle(self.mac2,s)
		
	    
		if int(control ) == 1:
			
			c1.switch_on()
			print "LUCE ACCESAAAAAAAAAAAAAAAAAAAA"

		else: 

			c1.switch_off()
			
			
	def Halert (self, alert):
	
	    #Halert_json = {"v": 1}                  or 0
	
		 self.humidityalert = alert
		 print alert
		 
		 
		 
	
 

