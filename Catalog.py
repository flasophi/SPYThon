# The Catalog is accessible through REST web services.
# The broker is identified with broker_IP and broker_port. It is set as written in the Catalog.txt file.
# Users are stored as: ID, nickname.
# Devices can be terraria or control strategies.
# - GET: - /broker/ -> Retrieve information about IP address and port of the message broker in the platform
#        - /terraria/ -> Retrieve list of registered terraria
#        - /terrarium?ID=<id> -> Retrieve information about a terrarium with a specific id
#        - /users/ -> Retrieve list of registered users
#        - /user?ID=<id> -> Retrieve information about a user with a specific id
#        - associate?IDTerr=<IDTerrarium>&IDUs=<IDUser> -> Associate a terrarium to a user
#        - changetemp?IDTerr=<IDTerrarium>&temp=<temp>
#        - changelightcycle?IDTerr=<IDTerrarium>&begin=<hour_begin>&duration=<durationhours>

#
# - POST: - /add_device/terrarium     ->  Registration or update of a terrarium
#         - /add_device/tempcontrol   ->  Registration or update of a control (can be done only by the control itself)
#         - /add_device/lightcontrol  ->  Registration or update of a control (can be done only by the control itself)
#         - /add_user/                -> Registration or update of a user
#
# -DELETE: - /device/terrarium    -> delete a device (done automatically every 2 minutes for devices older than 30 minutes)
#          - /device/tempcontrol  -> delete a device (done automatically every 2 minutes for devices older than 30 minutes)
#          - /device/lightcontrol -> delete a device (done automatically every 2 minutes for devices older than 30 minutes)
#          - /user/               -> delete a user


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

        # Initializes the first version of the catalog file containing the configured broker_IP and broker_port,
        # no users no terraria registered yet
        file = open(filename, 'r')
        dict_old = json.loads(file.read())
        file.close()
        dict_new = {'broker_IP': dict_old['broker_IP'], 'broker_port': dict_old['broker_port'],
                'terraria': [], 'temp_controls': [], 'light_controls': [], 'users': [] }
        file = open(filename, 'w')
        file.write(json.dumps(dict_new))
        file.close()

    ## WEB SERVICE
    def GET(self, *uri, **params):

        file = open(filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        if len(uri) == 0:
            raise cherrypy.HTTPError(400)

        # /broker/ -> Retrieve information about IP address and port of the message broker in the platform
        if uri[0] == 'broker':
            out_dict = {'broker_IP': dict['broker_IP'],
            'broker_port': dict['broker_port']}
            return json.dumps(out_dict)

        # /terraria/ -> Retrieve list of registered devices
        elif uri[0] == 'terraria':
            return json.dumps(dict['terraria'])

        # /terrarium?ID=<id> -> Retrieve information about a device with a specific id
        elif uri[0] == 'terrarium':
            for device in dict['terraria']:
                if device['ID'] == params['ID']:
                    return json.dumps(device)
            raise cherrypy.HTTPError(404)

        # /users/ -> Retrieve list of registered users
        elif uri[0] == 'users':
            return json.dumps(dict['users'])

        # /user?ID=<id> -> Retrieve information about a user with a specific id
        elif uri[0] == 'user':
            for user in dict['users']:
                if user['ID'] == params['ID']:
                    return json.dumps(user)
            raise cherrypy.HTTPError(404)

        # /associate?IDTerr=<IDTerrarium>&IDUs=<IDUser> -> Associate a terrarium to a user
        elif uri[0] == 'associate':
            flag = 0
            for user in dict['users']:
                if user['ID'] == params['IDUs']:
                    flag = 1
            if flag == 0:
                raise cherrypy.HTTPError(404)

            for terr in dict['terraria']:
                if terr['ID'] == params['IDTerr']:
                    terr['user'] = params['IDUs']
                    threadLock.acquire()
                    file = open(filename, 'w')
                    file.write(json.dumps(dict))
                    file.close()
                    threadLock.release()
                    return

            raise cherrypy.HTTPError(404)

        elif uri[0] == 'changetemp':
            for ctrl in dict['temp_controls']:
                if ctrl['terrarium'] == params['IDTerr']:
                    if params['temp'] != 'null':
                        ctrl['temp'] = params['temp']
                    else:
                        ctrl['temp'] = None
                    threadLock.acquire()
                    file = open(filename, 'w')
                    file.write(json.dumps(dict))
                    file.close()
                    threadLock.release()
                    return
            raise cherrypy.HTTPError(404)

        elif uri[0] == 'changelightcycle':
            for ctrl in dict['light_controls']:

                if ctrl['terrarium'] == params['IDTerr']:
                    if params['dawn'] != 'null':
                        ctrl['dawn'] = params['dawn']
                        ctrl['dusk'] = params['dusk']
                    else:
                        ctrl['dawn'] = None
                        ctrl['dusk'] = None

                    threadLock.acquire()
                    file = open(filename, 'w')
                    file.write(json.dumps(dict))
                    file.close()
                    threadLock.release()

                    try:
                        r = requests.get('http://' + ctrl['IP'] + ':8080/light/', params = {'dawn': ctrl['dawn'], 'dusk': ctrl['dusk']})
                        r.raise_for_status()
                    except requests.HTTPError as err:
                        raise cherrypy.HTTPError(500)
                        return

                    return
            raise cherrypy.HTTPError(404)

        else:
            raise cherrypy.HTTPError(400)

    def POST(self, *uri):

        if len(uri) == 0:
            raise cherrypy.HTTPError(400)
        # Reads POST request body
        mybody = cherrypy.request.body.read()

        try:
            data = json.loads(mybody)
        except:
            raise cherrypy.HTTPError(400)

        # Acquires lock to access the catalog file
        threadLock.acquire()

        file = open(filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        # /add_device/ ->  Registration or update of a device
        if uri[0] == 'add_device':

            if uri[1] == 'terrarium':

                for device in dict['terraria']:
                    if device['ID'] == data['ID']:
                        try:
                            device['IP'] = data['IP']
                            device['GET'] = data['GET']
                            device['POST'] = data['POST']
                            device['sub_topics'] = data['sub_topics']
                            device['pub_topics'] = data['pub_topics']
                            device['resources'] = data['resources']
                            device['insert-timestamp'] = time.time()
                        except:
                            threadLock.release()
                            raise cherrypy.HTTPError(400)

                        file = open(filename, 'w')
                        file.write(json.dumps(dict))
                        file.close()
                        threadLock.release()
                        return

                try:
                    dict['terraria'].append({'ID': data['ID'],
                                        'IP': data['IP'],
                                        'GET': data['GET'],
                                        'POST': data['POST'],
                                        'sub_topics': data['sub_topics'],
                                        'pub_topics': data['pub_topics'],
                                        'resources': data['resources'],
                                        'user': None,
                                        'insert-timestamp': time.time()})
                except:
                    threadLock.release()
                    raise cherrypy.HTTPError(400)

            elif uri[1] == 'tempcontrol':
                print data
                for device in dict['temp_controls']:
                    if device['ID'] == data['ID']:
                        try:
                            device['IP'] = data['IP']
                            device['GET'] = data['GET']
                            device['POST'] = data['POST']
                            device['sub_topics'] = data['sub_topics']
                            device['pub_topics'] = data['pub_topics']
                            device['temp'] = data['temp']
                            device['terrarium'] = data['terrarium']
                            device['insert-timestamp'] = time.time()
                        except:
                            threadLock.release()
                            raise cherrypy.HTTPError(400)
                        file = open(filename, 'w')
                        file.write(json.dumps(dict))
                        file.close()
                        threadLock.release()
                        return

                try:
                    dict['temp_controls'].append({'ID': data['ID'],
                                        'IP': data['IP'],
                                        'GET': data['GET'],
                                        'POST': data['POST'],
                                        'sub_topics': data['sub_topics'],
                                        'pub_topics': data['pub_topics'],
                                        'temp': data['temp'],
                                        'terrarium': data['terrarium'],
                                        'insert-timestamp': time.time()})
                except:
                    threadLock.release()
                    raise cherrypy.HTTPError(400)

            elif uri[1] == 'lightcontrol':

                for device in dict['light_controls']:
                    if device['ID'] == data['ID']:
                        try:
                            device['IP'] = data['IP']
                            device['GET'] = data['GET']
                            device['POST'] = data['POST']
                            device['sub_topics'] = data['sub_topics']
                            device['pub_topics'] = data['pub_topics']
                            device['dawn'] = data['dawn']
                            device['dusk'] = data['dusk']
                            device['terrarium'] = data['terrarium']
                            device['insert-timestamp'] = time.time()
                        except:
                            threadLock.release()
                            raise cherrypy.HTTPError(400)
                        file = open(filename, 'w')
                        file.write(json.dumps(dict))
                        file.close()
                        threadLock.release()
                        return

                try:
                    dict['light_controls'].append({'ID': data['ID'],
                                        'IP': data['IP'],
                                        'GET': data['GET'],
                                        'POST': data['POST'],
                                        'sub_topics': data['sub_topics'],
                                        'pub_topics': data['pub_topics'],
                                        'dawn': data['dawn'],
                                        'dusk': data['dusk'],
                                        'terrarium': data['terrarium'],
                                        'insert-timestamp': time.time()})
                except:
                    threadLock.release()
                    raise cherrypy.HTTPError(400)


            else:
                threadLock.release()
                raise cherrypy.HTTPError(400)

            file = open(filename, 'w')
            file.write(json.dumps(dict))
            file.close()

        # /add_user/ -> Registration or update of a user
        elif uri[0] == 'add_user':
            for user in dict['users']:
                if user['ID'] == data['ID']:
                    user['nickname'] = data['nickname']
                    file = open(filename, 'w')
                    file.write(json.dumps(dict))
                    file.close()
                    threadLock.release()
                    return

            try:
                dict['users'].append({'ID': data['ID'],
                                    'nickname': data['nickname']})
            except:
                threadLock.release()
                raise cherrypy.HTTPError(400)

            file = open(filename, 'w')
            file.write(json.dumps(dict))
            file.close()

        else:
            threadLock.release()
            raise cherrypy.HTTPError(400)

        threadLock.release()

    def DELETE(self, *uri, **params):

        threadLock.acquire()

        try:
            ID = params['ID']
        except:
            threadLock.release()
            raise cherrypy.HTTPError(400)

        file = open(filename, 'r')
        dict = json.loads(file.read())
        file.close()

        # /device/ -> delete a device
        if uri[0] == 'device':
            if uri[1] == 'terrarium':
                for device in dict['terraria']:
                    if device['ID'] == ID:
                        dict['terraria'].remove(device)
                        file = open(filename, 'w')
                        file.write(json.dumps(dict))
                        file.close()
                        break

            elif uri[1] == 'tempcontrol':
                for device in dict['temp_controls']:
                    if device['ID'] == ID:
                        dict['temp_controls'].remove(device)
                        file = open(filename, 'w')
                        file.write(json.dumps(dict))
                        file.close()
                        break

            elif uri[1] == 'lightcontrol':
                for device in dict['light_controls']:
                    if device['ID'] == ID:
                        dict['light_controls'].remove(device)
                        file = open(filename, 'w')
                        file.write(json.dumps(dict))
                        file.close()
                        break

            else:
                threadLock.release()
                raise cherrypy.HTTPError(400)

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
            threadLock.release()
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

            for device in dict['terraria']:
                if time.time() - device['insert-timestamp'] > 1800:
                    URL = 'http://localhost:8080/device/terrarium'
                    params = {'ID': device['ID']}
                    try:
            			r = requests.delete(URL, params = params)
            			r.raise_for_status()
                    except requests.HTTPError as err:
                        print err

            for device in dict['temp_controls']:
                if time.time() - device['insert-timestamp'] > 1800:
                    URL = 'http://localhost:8080/device/tempcontrol'
                    params = {'ID': device['ID']}
                    try:
            			r = requests.delete(URL, params = params)
            			r.raise_for_status()
                    except requests.HTTPError as err:
                        print err

            for device in dict['light_controls']:
                if time.time() - device['insert-timestamp'] > 1800:
                    URL = 'http://localhost:8080/device/lightcontrol'
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
