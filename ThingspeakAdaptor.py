### this scripts has to receive from MQTT data sensor in SenML format
### and post via HTTP request in my ThingSpeak Channels


import request
import urrlib
import thingspeak
import threading

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
        self.temperatureHistory = dict();
        self.humidityHistory = dict();
        self.light_statusHistory = dict();
        self.lock_statusHistory = dict();
		# register the callback
		self._paho_mqtt.on_connect = self.myOnConnect
		self._paho_mqtt.on_message = self.myOnMessageReceived
        self.temperatureChannel = thingspeak.Channel(id = 680372, api_key = "AFD10RO5MXMAS7XU").get_field(1)
        self.humidityChannel = thingspeak.Channel(id = 680372, api_key = "U5K874E6RLTA6PCE").get_field(2)
        self.light_statusChannel = thingspeak.Channel(id = 682373, api_key = "ZD53DI3U33KNB9D4").get_field(1)
        self.lock_statusChannel = thingspeak.Channel(id = 682369, api_key = "ZD53DI3U33KNB9D4").get_field(1)

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

        if (msg.topic == 'SPYthon/'+ self.deviceID +"/temperature"):
            ControlHistory c = ControlHistory(temperatureHistory)
            dataReceived = json.loads(msg.payload)
            if temperatureHistory is None:
                temperatureHistory.update(dataReceived)
            else :
                temperatureHistory['e'].append(dataReceived['e'])
            c.start()
            temperatureChannel.update(json.dumps(dataReceived))

        elif (msg.topic =='SPYthon/'+ self.deviceID +"/humidity"):
            ControlHistory c = ControlHistory(humidityHistory)
            dataReceived = json.loads(msg.payload)
            if humidityHistory is None:
                humidityHistory.update(dataReceived)
            else :
                humidityHistory['e'].append(dataReceived['e'])
            c.start()
            humidityHistory.update(json.dumps(dataReceived))


        elif (msg.topic == 'SPYthon/'+ self.deviceID +"/light_status"):
            ControlHistory c = ControlHistory(light_statusHistory)
            dataReceived = json.loads(msg.payload)
            if light_statusHistory is None:
                light_statusHistory.update(dataReceived)
            else :
                light_statusHistory['e'].append(dataReceived['e'])
            c.start()
            light_statusChannel.update(json.dumps(dataReceived))


        elif (msg.topic == 'SPYthon/'+ self.deviceID +"/lock_status"):
            ControlHistory c = ControlHistory(lock_statusHistory)
            dataReceived = json.loads(msg.payload)
            if lock_statusHistory is None:
                lock_statusHistory.update(dataReceived)
            else :
                lock_statusHistory['e'].append(dataReceived['e'])
            c.start()
            lock_statusChannel.update(json.dumps(dataReceived))

        


class ControlHistory(threading.Thread):
    def __init__(self,statusHistory):
        threading.Thread.__init__(self)
        self.statusHistory = statusHistory
        self.actualTime = datetime.datetime.fromtimestamp(time.time()/1000)
    def run(self):
        countGoodValues = 0;
        if statusHistory is not None:
            for (registration in statusHistory['e']):
                if countGoodValues > 10:
                    break
                registrationTime = datetime.datetime.fromtimestamp(registration["t"]/1000)
                delta_days = (actualTime - registrationTime).days
                if delta_days > 7:
                    statusHistory.remove(statusHistory['e'])
                else
                    countGoodValues = countGoodValues +1
