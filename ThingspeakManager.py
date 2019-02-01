### this scripts has to receive from MQTT data sensor in SenML format
### and post via HTTP request in my ThingSpeak Channels


import request
import urrlib
import thingspeak

#this class manages the messages arrived from MQTT, it's a subscriber
class ThingSpeakDataManager:
    def __init__(self, clientID, deviceID, broker, port,deviceconnector):
        #self.deviceconnector=deviceconnector
		#self.broker = broker
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

        # ThingSpeak
        self.temperatureChannel =

    def mySubscribe (self, topic):
		# if needed, you can do some computation or error-check before subscribing
		print ("subscribing to %s" % (topic))
		# subscribe for a topic
		self._paho_mqtt.subscribe(topic, 2)
		# just to remember that it works also as a subscriber
		self._isSubscriber = True
		self._topic = topic

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
            if (msg.topic == 'SPYthon/'+ self.deviceID +"/temperature"):
                data = urllib.urlopen("here I insert the TS url")


            elif (msg.topic =='SPYthon/'+ self.deviceID +"/humidity"):


            elif (msg.topic == 'SPYthon/'+ self.deviceID +"/light_status"):


            elif (msg.topic == 'SPYthon/'+ self.deviceID +"/lock_status"):


data = urllib.urlopen("here I insert the TS url")
