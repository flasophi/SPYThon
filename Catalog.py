# The Catalog is accessible through REST web services.
# The broker is identified with broker_IP and broker_port. It must be set with a POST request. At start-up both fields are None.
# Devices are stored as: ID, IP, GET (list of urls to access GET method), POST (list of urls to access POST method),
# sub_topics (list of MQTT topics which the device is subscribed to), pub_topics (list of MQTT topics for which the device publishes),
# resources (list of sensors/actuators), conf (configurations for the control strategies). If a field is empty it is None.
# Users are stored as: ID, name, surname and email.
# - GET: - /broker/ -> Retrieve information about IP address and port of the message broker in the platform
#        - /devices/ -> Retrieve list of registered devices
#        - /device?ID=<id> -> Retrieve information about a device with a specific id
#        - /users/ -> Retrieve list of registered users
#        - /user?ID=<id> -> Retrieve information about a user with a specific id
#
# - POST: - /register_broker/ -> Registration of the MQTT message broker (IP and port)
#         - /add_device/ ->  Registration or update of a device
#         - /add_user/ -> Registration or update of a user
#
# -DELETE: - /device/ -> delete a device (done automatically every 2 minutes for devices older than 30 minutes)
#          - /user/ -> delete a user


import cherrypy
import json
import time
import threading
import requests

threadLock = threading.Lock()
filename = "Catalog.txt"

## REST Web Service
class RESTCatalog:

    exposed = True

    def __init__(self):

        #### Creation of json file
        devices = []
        users = []
        dict = {'broker_IP': None, 'broker_port': None,
                'devices': devices, 'users': users}
        json_file = json.dumps(dict)
        file = open(filename, 'w')
        file.write(json_file)
        file.close()

    ## WEB SERVICE
    def GET(self, *uri, **params):

        file = open(filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)

        if len(uri) == 0:
            raise cherrypy.HTTPError(400)

        # /broker/ -> Retrieve information about IP address and port of the message broker in the platform
        if uri[0] == 'broker':
            out_dict = {'broker_IP': dict['broker_IP'],
            'broker_port': dict['broker_port']}
            return json.dumps(out_dict)

        # /devices/ -> Retrieve list of registered devices
        elif uri[0] == 'devices':
            return json.dumps(dict['devices'])

        # /device?ID=<id> -> Retrieve information about a device with a specific id
        elif uri[0] == 'device':
            for device in dict['devices']:
                if device['ID'] == params['ID']:
                    return json.dumps(device)

        # /users/ -> Retrieve list of registered users
        elif uri[0] == 'users':
            return json.dumps(dict['users'])

        # /user?ID=<id> -> Retrieve information about a user with a specific id
        elif uri[0] == 'user':
            for user in dict['users']:
                if user['ID'] == params['ID']:
                    return json.dumps(user)
        else:
            raise cherrypy.HTTPError(400)
        file.close()

    def POST(self, *uri):

        if len(uri) == 0:
            raise cherrypy.HTTPError(400)

        # Acquires lock to access the json
        threadLock.acquire()
        # Reads POST request body
        mybody = cherrypy.request.body.read()

        try:
            data = json.loads(mybody)
        except:
            raise cherrypy.HTTPError(400)

        file = open(filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        # /register_broker/ -> Registration of the MQTT message broker (IP and port)
        if uri[0] == 'register_broker':
            try:
                dict['broker_IP'] = data['broker_IP']
                dict['broker_port'] = data['broker_port']
            except:
                raise cherrypy.HTTPError(400)

            file = open(filename, 'w')
            file.write(json.dumps(dict))
            file.close()

        # /add_device/ ->  Registration or update of a device
        elif uri[0] == 'add_device':
            for device in dict['devices']:
                if device['ID'] == data['ID']:
                    try:
                        device['IP'] = data['IP']
                        device['GET'] = data['GET']
                        device['POST'] = data['POST']
                        device['sub_topics'] = data['sub_topics']
                        device['pub_topics'] = data['pub_topics']
                        device['resources'] = data['resources']
                        device['conf'] = data['conf']
                        device['insert-timestamp'] = time.time()
                    except:
                        raise cherrypy.HTTPError(400)

                    file = open(filename, 'w')
                    file.write(json.dumps(dict))
                    file.close()
                    threadLock.release()
                    return

            try:
                dict['devices'].append({'ID': data['ID'],
                                    'IP': data['IP'],
                                    'GET': data['GET'],
                                    'POST': data['POST'],
                                    'sub_topics': data['sub_topics'],
                                    'pub_topics': data['pub_topics'],
                                    'resources': data['resources'],
                                    'conf': data['conf'],
                                    'insert-timestamp': time.time()})
            except:
                raise cherrypy.HTTPError(400)

            file = open(filename, 'w')
            file.write(json.dumps(dict))
            file.close()

        # /add_user/ -> Registration or update of a user
        elif uri[0] == 'add_user':
            for user in dict['users']:
                if user['ID'] == data['ID']:
                    user['name'] = data['name']
                    user['surname'] = data['surname']
                    user['email'] = data['email']
                    file = open(filename, 'w')
                    file.write(json.dumps(dict))
                    file.close()
                    threadLock.release()
                    return

            dict['users'].append({'ID': data['ID'],
                                    'name': data['name'],
                                    'surname': data['surname'],
                                    'email': data['email']})
            file = open(filename, 'w')
            file.write(json.dumps(dict))
            file.close()

        else:
            raise cherrypy.HTTPError(400)

        threadLock.release()

    def DELETE(self, *uri, **params):

        threadLock.acquire()

        try:
            ID = params['ID']
        except:
            raise cherrypy.HTTPError(400)

        file = open(filename, 'r')
        dict = json.loads(file.read())
        file.close()

        # /device/ -> delete a device
        if uri[0] == 'device':
            for device in dict['devices']:
                if device['ID'] == ID:
                    dict['devices'].remove(device)
                    file = open(filename, 'w')
                    file.write(json.dumps(dict))
                    file.close()
                    break

        # /user/ -> delete a user
        elif uri[0] == 'user':
            for user in dict['users']:
                if user['ID'] == ID:
                    dict['users'].remove(user)
                    file = open(filename, 'w')
                    file.write(json.dumps(dict))
                    file.close()
                    break

        else:
            raise cherrypy.HTTPError(400)

        threadLock.release()


## Thread to delete old devices
class DeleteDevice(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:

            file = open(filename, 'r')
            dict = json.loads(file.read())
            file.close()

            for device in dict['devices']:
                if time.time() - device['insert-timestamp'] > 1800:
                    URL = 'http://localhost:8080/device/'
                    params = {'ID': device['ID']}
                    try:
            			r = requests.delete(URL, params = params)
            			r.raise_for_status()
                    except requests.HTTPError as err:
                        print err


            time.sleep(120)


if __name__ == '__main__':
	conf = {
		'/': {
		'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
		'tools.sessions.on': True,
	}
}

cherrypy.tree.mount (RESTCatalog(), '/', conf)
cherrypy.config.update({'server.socket_host': '0.0.0.0'})
cherrypy.config.update({'server.socket_port': 8080})
cherrypy.engine.start()

deletedevice = DeleteDevice()
deletedevice.start()
