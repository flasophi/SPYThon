import threading
import time
import json

# CATALOG. It implements a catalog with the following entries:
# broker_IP, broker_port, terraria, temperature controls (temp_controls), light_controls, users
# the catalog is initalized by reading the first version of the catalog json file
# each access to the json file is protected against multi-threading by a Lock
# a thread is automatically activated to delete devices (terraria and controls) which are not updated for more than 30 minutes, to prevent requests to wrong IP
# terraria are identified by: ID, IP, GET, POST, sub_topics, pub_topics, resources, user (ID of the associated user, None if not already associated), insert-timestamp
# temperature controls are identified by: ID, IP, GET, POST, sub_topics, pub_topics, temp, terrarium (ID of the associated terrarium), insert-timestamp
# light controls are identified by: ID, IP, GET, POST, sub_topics, pub_topics, dawn, dusk, terrarium (ID of the associated terrarium), insert-timestamp
# users are identified by a nickname (the one on Telegram) and by the chat_id to send messages on Telegram.

class Catalog:

    def __init__(self, filename):

        self.filename = filename

        file = open(self.filename, 'r')
        dict_old = json.loads(file.read())
        file.close()

        dict_new = {'broker_IP': dict_old['broker_IP'], 'broker_port': dict_old['broker_port'],
                'terraria': dict_old['terraria'], 'temp_controls': dict_old['temp_controls'], 'light_controls': dict_old['light_controls'],
                'users': dict_old['users'] }

        file = open(self.filename, 'w')
        file.write(json.dumps(dict_new))
        file.close()

        self.threadLock = threading.Lock()

        self.deletingThread = DeleteDevice(self)
        self.deletingThread.start()

    def broker(self):

        self.threadLock.acquire()

        file = open(self.filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        self.threadLock.release()

        return dict['broker_IP'], dict['broker_port']

    def terraria(self):

        self.threadLock.acquire()

        file = open(self.filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        self.threadLock.release()
        return dict['terraria']

    def terrarium(self, ID):
        self.threadLock.acquire()

        file = open(self.filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        self.threadLock.release()

        for device in dict['terraria']:
            if device['ID'] == ID:
                return device
        return "Terrarium not found"


    def users(self):
        self.threadLock.acquire()

        file = open(self.filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        self.threadLock.release()
        return dict['users']

    def user(self, ID):
        self.threadLock.acquire()

        file = open(self.filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()
        self.threadLock.release()

        for user in dict['users']:
            if user['ID'] == ID:
                return json.dumps(user)
        return "User not found"

    def associate(self, IDUser, IDTerr, password):

        self.threadLock.acquire()

        file = open(self.filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        # Search for the user
        flag = 0
        for user in dict['users']:
            if user['ID'] == IDUser:
                flag = 1
                break
        if flag == 0:
            self.threadLock.release()
            return "Error"


        for terr in dict['terraria']:
            if terr['ID'] == IDTerr:
                if terr['pws'] != password:
                    return "password incorrect"
                terr['user'] = IDUser
                file = open(self.filename, 'w')
                file.write(json.dumps(dict))
                file.close()
                self.threadLock.release()
                return "Done"

        # if terrarium is not found
        self.threadLock.release()
        return "Error"

    def changetemp(self, IDTerr, temp):

        self.threadLock.acquire()

        file = open(self.filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        for ctrl in dict['temp_controls']:

            if ctrl['terrarium'] == IDTerr:
                ctrl['temp'] = temp

                file = open(self.filename, 'w')
                file.write(json.dumps(dict))
                file.close()
                self.threadLock.release()
                return ctrl['IP'], ctrl['port']

        # if the control for that terrarium is not found
        self.threadLock.release()
        return "Error", "Error"

    def changelightcycle(self, IDTerr, dawn, dusk):

        self.threadLock.acquire()

        file = open(self.filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        for ctrl in dict['light_controls']:

            if ctrl['terrarium'] == IDTerr:

                ctrl['dawn'] = dawn
                ctrl['dusk'] = dusk

                file = open(self.filename, 'w')
                file.write(json.dumps(dict))
                file.close()
                self.threadLock.release()

                return ctrl['IP'], ctrl['port']

        # if the control for that terrarium is not found
        self.threadLock.release()
        return "Error", "Error"


    def addterrarium(self, data):

        self.threadLock.acquire()

        file = open(self.filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        for device in dict['terraria']:
            try:
                if device['ID'] == data['ID']:
                    device['IP'] = data['IP']
                    device['port'] = data['port']
                    device['GET'] = data['GET']
                    device['POST'] = data['POST']
                    device['sub_topics'] = data['sub_topics']
                    device['pub_topics'] = data['pub_topics']
                    device['resources'] = data['resources']
                    device['pws'] = data['psw']
                    device['insert-timestamp'] = time.time()
                    file = open(self.filename, 'w')
                    file.write(json.dumps(dict))
                    file.close()
                    self.threadLock.release()
                    return "Update done"
            except:
                self.threadLock.release()
                return "Error"

        try:
            dict['terraria'].append({'ID': data['ID'],
                                'IP': data['IP'],
                                'port': data['port'],
                                'GET': data['GET'],
                                'POST': data['POST'],
                                'sub_topics': data['sub_topics'],
                                'pub_topics': data['pub_topics'],
                                'resources': data['resources'],
                                'pws': data['psw'],
                                'user': None,
                                'insert-timestamp': time.time()})

            file = open(self.filename, 'w')
            file.write(json.dumps(dict))
            file.close()
            self.threadLock.release()
            return "Registration done"
        except:
            self.threadLock.release()
            return "Error"

    def addtempcontrol(self, data):

        self.threadLock.acquire()

        file = open(self.filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        for device in dict['temp_controls']:
            if device['ID'] == data['ID']:
                try:
                    device['IP'] = data['IP']
                    device['port'] = data['port']
                    device['GET'] = data['GET']
                    device['POST'] = data['POST']
                    device['sub_topics'] = data['sub_topics']
                    device['pub_topics'] = data['pub_topics']
                    device['temp'] = data['temp']
                    device['terrarium'] = data['terrarium']
                    device['insert-timestamp'] = time.time()

                    file = open(self.filename, 'w')
                    file.write(json.dumps(dict))
                    file.close()
                    self.threadLock.release()
                    return "Update done"
                except:
                    self.threadLock.release()
                    return "Error"

        try:
            dict['temp_controls'].append({'ID': data['ID'],
                                'IP': data['IP'],
                                'port': data['port'],
                                'GET': data['GET'],
                                'POST': data['POST'],
                                'sub_topics': data['sub_topics'],
                                'pub_topics': data['pub_topics'],
                                'temp': data['temp'],
                                'terrarium': data['terrarium'],
                                'insert-timestamp': time.time()})

            file = open(self.filename, 'w')
            file.write(json.dumps(dict))
            file.close()
            self.threadLock.release()
            return "Registration done"
        except:
            self.threadLock.release()
            return "Error"

    def addlightcontrol(self, data):

        self.threadLock.acquire()

        file = open(self.filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        for device in dict['light_controls']:
            try:
                if device['ID'] == data['ID']:
                    device['IP'] = data['IP']
                    device['port'] = data['port']
                    device['GET'] = data['GET']
                    device['POST'] = data['POST']
                    device['sub_topics'] = data['sub_topics']
                    device['pub_topics'] = data['pub_topics']
                    device['dawn'] = data['dawn']
                    device['dusk'] = data['dusk']
                    device['terrarium'] = data['terrarium']
                    device['insert-timestamp'] = time.time()

                    file = open(self.filename, 'w')
                    file.write(json.dumps(dict))
                    file.close()
                    self.threadLock.release()
                    return "Update done"
            except:
                self.threadLock.release()
                return "Error"

        try:
            dict['light_controls'].append({'ID': data['ID'],
                                'IP': data['IP'],
                                'port': data['port'],
                                'GET': data['GET'],
                                'POST': data['POST'],
                                'sub_topics': data['sub_topics'],
                                'pub_topics': data['pub_topics'],
                                'dawn': data['dawn'],
                                'dusk': data['dusk'],
                                'terrarium': data['terrarium'],
                                'insert-timestamp': time.time()})

            file = open(self.filename, 'w')
            file.write(json.dumps(dict))
            file.close()
            self.threadLock.release()
            return "Registration done"
        except:
            self.threadLock.release()
            return "Error"

    def adduser(self, data):

        self.threadLock.acquire()

        file = open(self.filename, 'r')
        json_file = file.read()
        dict = json.loads(json_file)
        file.close()

        for user in dict['users']:
            try:
                if user['ID'] == str(data['ID']):
                    user['nickname'] = data['nickname']
                    file = open(self.filename, 'w')
                    file.write(json.dumps(dict))
                    file.close()
                    self.threadLock.release()
                    return "Update done"
            except:
                self.threadLock.release()
                return "Error"

        try:
            dict['users'].append({'ID': str(data['ID']),
                                'nickname': data['nickname']})
            file = open(self.filename, 'w')
            file.write(json.dumps(dict))
            file.close()
            self.threadLock.release()
            return "Registration done"
        except:
            self.threadLock.release()
            return "Error"

    def deleteterrarium(self, ID):

        self.threadLock.acquire()

        print "Deleting terrarium"
        file = open(self.filename, 'r')
        dict = json.loads(file.read())
        file.close()

        for device in dict['terraria']:
            if device['ID'] == ID:
                dict['terraria'].remove(device)
                file = open(self.filename, 'w')
                file.write(json.dumps(dict))
                file.close()
                break

        self.threadLock.release()

    def deletetempcontrol(self, ID):

        self.threadLock.acquire()

        file = open(self.filename, 'r')
        dict = json.loads(file.read())
        file.close()

        for device in dict['temp_controls']:
            if device['ID'] == ID:
                dict['temp_controls'].remove(device)
                file = open(self.filename, 'w')
                file.write(json.dumps(dict))
                file.close()
                break

        self.threadLock.release()


    def deletelightcontrol(self, ID):

        self.threadLock.acquire()

        file = open(self.filename, 'r')
        dict = json.loads(file.read())
        file.close()

        for device in dict['light_controls']:
            if device['ID'] == ID:
                dict['light_controls'].remove(device)
                file = open(self.filename, 'w')
                file.write(json.dumps(dict))
                file.close()
                break

        self.threadLock.release()


    def deleteuser(self, ID):

        self.threadLock.acquire()

        file = open(self.filename, 'r')
        dict = json.loads(file.read())
        file.close()

        for terrarium in dict['terraria']:
            if terrarium['user'] == ID:
                terrarium['user'] = None

        for user in dict['users']:
            if user['ID'] == ID:
                dict['users'].remove(user)
                break

        file = open(self.filename, 'w')
        file.write(json.dumps(dict))
        file.close()

        self.threadLock.release()


## Thread to delete devices older than half an hour
class DeleteDevice(threading.Thread):

    def __init__(self, catalog):
        threading.Thread.__init__(self)
        self.catalog = catalog

    def run(self):
        while True:

            self.catalog.threadLock.acquire()
            file = open(self.catalog.filename, 'r')
            dict = json.loads(file.read())
            file.close()
            self.catalog.threadLock.release()

            for device in dict['terraria']:
                if time.time() - device['insert-timestamp'] > 30*60:
                    self.catalog.deleteterrarium(device['ID'])

            for device in dict['temp_controls']:
                if time.time() - device['insert-timestamp'] > 30*60:
                    self.catalog.deletetempcontrol(device['ID'])

            for device in dict['light_controls']:
                if time.time() - device['insert-timestamp'] > 30*60:
                    self.catalog.deletelightcontrol(device['ID'])

            time.sleep(10)
