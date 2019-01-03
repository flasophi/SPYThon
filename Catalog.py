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

        # Registration of the MQTT message broker (IP and port)
        if uri[0] == 'register_broker':
            try:
                dict['broker_IP'] = data['broker_IP']
                dict['broker_port'] = data['broker_port']
            except:
                raise cherrypy.HTTPError(400)

            file = open(filename, 'w')
            file.write(json.dumps(dict))
            file.close()

        # Registration or update of a device
        elif uri[0] == 'add_device':
            for device in dict['devices']:
                if device['ID'] == data['ID']:
                    try:
                        device['GET'] = data['GET']
                        device['POST'] = data['POST']
                        device['topics'] = data['topics']
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
                                    'GET': data['GET'],
                                    'POST': data['POST'],
                                    'topics': data['topics'],
                                    'resources': data['resources'],
                                    'conf': data['conf'],
                                    'insert-timestamp': time.time()})
            except:
                raise cherrypy.HTTPError(400)

            file = open(filename, 'w')
            file.write(json.dumps(dict))
            file.close()

        # Registration or update of a user
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

    def DELETE(self, **params):
        threadLock.acquire()

        try:
            ID = params['ID']
        except:
            raise cherrypy.HTTPError(400)

        file = open(filename, 'r')
        dict = json.loads(file.read())
        file.close()

        for device in dict['devices']:
            if device['ID'] == ID:
                dict['devices'].remove(device)
                #print 'Removed a device'
                file = open(filename, 'w')
                file.write(json.dumps(dict))
                file.close()
                break

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
                    URL = 'http://localhost:8080/'
                    params = {'ID':device['ID']}
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
