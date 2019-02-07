### this scripts has to receive from MQTT data sensor in SenML format
### and post via HTTP request in my ThingSpeak Channels

import thingspeak
import threading
import json
import paho.mqtt.client as PahoMQTT
import datetime
import time
import requests
import sys
import urllib
from bs4 import BeautifulSoup

#this class manages the messages arrived from MQTT, it's a subscriber
class ThingSpeakDataManager :
    def __init__(self, deviceID, broker, port):
        self.deviceID = deviceID
        self.broker = broker
        self.port = port
        self.topic = "" 
        self._isSubscriber = False
        self._paho_mqtt = PahoMQTT.Client(deviceID, False)
        self.temperatureHistory = {"write_api_key": "AFD10RO5MXMAS7XU", "updates": []}
        self.humidityHistory = {"write_api_key": "J4GGNYGH12CM8ZGY", "updates": []}
        self.light_statusHistory = {"write_api_key": "U5K874E6RLTA6PCE", "updates": []}
        self.lock_statusHistory = {"write_api_key": "ZD53DI3U33KNB9D4", "updates": []}
        self.databases = [self.temperatureHistory, self.humidityHistory, self.light_statusHistory, self.lock_statusHistory ]
		# register the callback
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived
        
    def mySubscribe (self, topic):
		# if needed, you can do some computation or error-check before subscribing
        topic_jolly = "/SPYthon/nagini/+"
        print ("subscribing to %s" % (topic))
		# subscribe for a topic
        self._isSubscriber = True
        self._paho_mqtt.subscribe(topic_jolly, 2)
		# just to remember that it works also as a subscribe
        self._topic = topic

    def myOnConnect (self, paho_mqtt, userdata, flags, rc):
		print ("Connected to %s with result code: %d" % (self.broker, rc))

    def myOnMessageReceived (self, paho_mqtt , userdata, msg):
        print ("!")
        print (msg.topic, msg.payload)
        print msg.topic
        print msg.payload

        msg_dict = json.loads(msg.payload.decode('string-escape').strip('"'))
        #datetime_stamp = datetime.datetime.fromtimestamp(msg_dict["e"]["t"])
        value = msg_dict["e"]["v"]
        #element_to_append = {"created_at": datetime_stamp, "field1" : value}

        if (msg.topic == '/SPYthon/'+ self.deviceID +"/temperature") :
            self.temperatureHistory["updates"].append(value)
            #dataJson = json.dumps(self.temperatureHistory)
            #requests.post("https://api.thingspeak.com/channels/680372/bulk_update.json", data=dataJson)
            data = urllib.urlopen("https://api.thingspeak.com/update?api_key=AFD10RO5MXMAS7XU&field1="+str(value))
            print ("value updated")
            print data
        elif (msg.topic =='/SPYthon/'+ self.deviceID +"/humidity"):
            self.humidityHistory["updates"].append(value)
            #dataJson = json.dumps(self.humidityHistory)
            #requests.post("https://api.thingspeak.com/channels/686718/bulk_update.json", data=dataJson)
            data = urllib.urlopen("https://api.thingspeak.com/update?api_key=J4GGNYGH12CM8ZGY&field1="+str(value))
            print ("value updated")
            print data
        elif (msg.topic == '/SPYthon/'+ self.deviceID +"/light_status"):
            self.light_statusHistory["updates"].append(value)
            #dataJson = json.dumps(self.light_statusHistory)
            #requests.post("https://api.thingspeak.com/channels/682373/bulk_update.json", data=dataJson)
            data = urllib.urlopen("https://api.thingspeak.com/update?api_key=U5K874E6RLTA6PCE&field1="+str(value))
            print ("value updated")
            print data
        elif (msg.topic == '/SPYthon/'+ self.deviceID +"/lock_status"):
            self.lock_statusHistory["updates"].append(value)
            #dataJson = json.dumps(self.lock_statusHistory)
            #requests.post("https://api.thingspeak.com/channels/682369/bulk_update.json", data=dataJson)
            data = urllib.urlopen("https://api.thingspeak.com/update?api_key=ZD53DI3U33KNB9D4&field1="+str(value))
            print ("value updated")
            print data

    def start(self):
		#manage connection to broker
		self._paho_mqtt.connect(self.broker , self.port)
		self._paho_mqtt.loop_start()
        print ("has started")

    def stop (self):
        if self._isSubscriber :
            self._paho_mqtt.unsubscribe(self.topic)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()


class ControlHistory(threading.Thread):
    def __init__(self,tsdm):
        threading.Thread.__init__(self)
        self.tsdm = tsdm
        self.actualTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    def run(self) :
        while True:
            for db in self.tsdm.databases:
                countGoodValues = 0
                if len(db["updates"]) > 10:
                    for value in db["updates"]:
                        if countGoodValues > 10 :
                            break
                        registrationTime = value["created_at"]
                        delta_days = self.actualTime - registrationTime
                        td = int(round(delta_days.total_seconds() / (60*60*24)))
                        if td > 7:
                            db["updates"].remove(value)
                        else:
                            countGoodValues = countGoodValues +1
                        
            time.sleep(300)


if __name__ == "__main__":

    conf_file = open("config.txt", 'r')
    conf_file_dict = json.loads(conf_file.read())
    conf_file.close()
    deviceID = conf_file_dict['deviceID']
    catalogIP = conf_file_dict['catalogIP']

    try:
		r2 = requests.get('http://'+ catalogIP + ':8080/broker')
		r2.raise_for_status()

		brokerip = r2.json()['broker_IP']
		print brokerip
		brokerport = r2.json()['broker_port']
    except requests.HTTPError as err:
            print 'Error in posting, aborting' 
            sys.exit()

    tdsm = ThingSpeakDataManager(deviceID, brokerip, brokerport)
    #control = ControlHistory(tdsm)
    tdsm.start()
    time.sleep(2)
    tdsm.mySubscribe('/#')
    #tdsm.mySubscribe('/SPYthon/'+ tdsm.deviceID +"/+")
    #tdsm.mySubscribe('/SPYthon/'+ tdsm.deviceID +"/humidity")
    #tdsm.mySubscribe('/SPYthon/'+ tdsm.deviceID +"/light_status")
    #tdsm.mySubscribe('/SPYthon/'+ tdsm.deviceID +"/lock_status")
    #control.start()
    while True:
        time.sleep(1)