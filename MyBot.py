import telepot
import time
from telepot.loop import MessageLoop
import requests
import json
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import re
import threading
import urllib2

class MyBot:

    def __init__(self, conf_file):

        file = open(conf_file, 'r')
        dict = json.loads(file.read())
        file.close()

        # Variables that keep track of a conversation
        self.send1 = 0
        self.send2 = 0
        self.terr = None

        self.token = dict['token']
        self.catalogIP = dict['catalog_IP']
        self.catalogport = str(dict['catalog_port'])
        self.bot = telepot.Bot(token=str(self.token))

        MessageLoop(self.bot, {'chat': self.on_chat_message, 'callback_query': self.on_callback_query}).run_as_thread()

        # Thread to alert users for incorrect value of humidity
        hum_alert = HumidityAlert(self)
        hum_alert.start()

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        if content_type == 'text':

            name = msg["from"]["first_name"]
            command = msg['text']

            if command == '/start':
                self.bot.sendMessage(chat_id, "Hello " + name +
                                    "! I'm your SPYThon bot. Please register yourself with /registermyself to get started.")

            elif command == '/help':
                self.bot.sendMessage(chat_id, """First you can register with: /registermyself. \n When you have your ID, you can use: /registerterrarium <myID> <terrariumID> to become the only owner of the terrarium..\n
                 Then you can check how your reptile is doing by: /check <myID> <terrariumID>.\n If you want to set the temperature control just type:
                 /controltemperature <myID> <terrariumID>, and if you wish to set the dawn and dusk hours of your terrarium type:
                 /controllightcycle <myID> <terrariumID>""")

            elif command == '/registermyself':         # Register the speaker as a user
                # Find the first available user ID
                try:
                    cnt = 0
                    while True:
                        ID = 'user' + str(cnt)
                        r = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/user/', params = {'ID': ID})
                        r.raise_for_status()
                        cnt += 1
                except requests.HTTPError as err:
                    if err.response.status_code != 404:
                        return

                payload = {'ID':ID, 'nickname':name, 'chat_id': chat_id}
                URL = 'http://' + self.catalogIP + ':' + self.catalogport + '/add_user'
                try:
                    r = requests.post(URL, data = json.dumps(payload))
                    r.raise_for_status()
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again.')
                    print err
                    return

                self.bot.sendMessage(chat_id, "Congratulations " + name +
                                    "! You have been registered with ID: " + ID +
                                    ". Please remember it and use it to identify yourself.")



            elif command.startswith('/registerterrarium'):  # Associate a terrarium (identified by its ID)
                                                            # to the speaker, who must give his/her ID.
                                                            # If the speaker or the terrarium are not registered, raise an error.

                params_bot = command.split(' ')[1:]
                if len(params_bot) < 2:
                    self.bot.sendMessage(chat_id, 'The correct syntax is: /registerterrarium myID terrariumID')
                    return

                payload = {'IDTerr':params_bot[1], 'IDUs':params_bot[0]}
                URL = 'http://' + self.catalogIP + ':' + self.catalogport + '/associate/'
                try:
                    r = requests.get(URL, params = payload)
                    r.raise_for_status()
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again. (syntax is: /registerterrarium myID terrariumID)')
                    print err
                    return

                self.bot.sendMessage(chat_id, "Congratulations " + name +
                                    "! The terrarium " + params_bot[1] + " has been associated to user " + params_bot[0] +
                                    ". Only this user has the right to access to the terrarium.")

            elif command.startswith('/check'):
                params_bot = command.split()[1:]

                if len(params_bot) < 2:
                    self.bot.sendMessage(chat_id, 'Correct syntax is: /check myID terrariumID')
                    return

                try:
                    r1 = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/terrarium/', params = {'ID': params_bot[1]})
                    r1.raise_for_status()
                    terr = r1.json()['terrarium']
                    if terr['user'] != params_bot[0]:
                        self.bot.sendMessage(chat_id, "This user can't check the terrarium. Please associate the user to the terrarium.")
                        return
                    r2 = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/user/', params = {'ID': params_bot[0]})
                    r2.raise_for_status()
                    user = r2.json()['user']
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again. (Correct syntax is: /check myID terrariumID)')
                    print err
                    return


                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                     [InlineKeyboardButton(text='Photo', callback_data='photo_' + terr['IP'] + '_' + terr['port']),
                     InlineKeyboardButton(text='Temperature', callback_data='temp_' + terr['IP'] + '_' + terr['port'])],
                     [InlineKeyboardButton(text='Humidity', callback_data='hum_' + terr['IP'] + '_' + terr['port']),
                     InlineKeyboardButton(text='Lock Status', callback_data='lock_' + terr['IP'] + '_' + terr['port'])]])

                self.bot.sendMessage(chat_id, 'What do you want to see?', reply_markup=keyboard)

            elif command.startswith('/controltemperature'):
                params_bot = command.split()[1:]

                if len(params_bot) < 2:
                    self.bot.sendMessage(chat_id, 'Correct syntax is: /controltemperature myID terrariumID')
                    return

                try:
                    r1 = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/terrarium/', params = {'ID': params_bot[1]})
                    r1.raise_for_status()
                    self.terr = r1.json()['terrarium']
                    if self.terr['user'] != params_bot[0]:
                        self.bot.sendMessage(chat_id, "This user can't control the terrarium. Please associate the user to the terrarium.")
                        return
                    r2 = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/user/', params = {'ID': params_bot[0]})
                    r2.raise_for_status()
                    user = r2.json()['user']
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again. (syntax is: /controltemperature myID terrariumID)')
                    return

                self.send1 = self.bot.sendMessage(chat_id, 'Please type the reference temperature or type STOP to deactivate the control.')

            elif command.startswith('/controllightcycle'):
                params_bot = command.split()[1:]

                if len(params_bot) < 2:
                    self.bot.sendMessage(chat_id, 'Correct syntax is: /controllightcycle myID terrariumID')
                    return

                try:
                    r1 = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/terrarium/', params = {'ID': params_bot[1]})
                    r1.raise_for_status()
                    self.terr = r1.json()['terrarium']
                    if self.terr['user'] != params_bot[0]:
                        self.bot.sendMessage(chat_id, "This user can't control the terrarium. Please associate the user to the terrarium.")
                        return
                    r2 = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/user/', params = {'ID': params_bot[0]})
                    r2.raise_for_status()
                    user = r2.json()['user']
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again. (syntax is: /controllightcycle myID terrariumID)')
                    return

                self.send2 = self.bot.sendMessage(chat_id, 'Please type the times in which you want the light to turn on and off (HH:MM) or type STOP to deactivate the control.')

            else:

                # Conversation about reference temperature
                if self.send1:

                    self.send1 = 0
                    if msg['text'] == 'STOP':
                        temp = 'null'
                    else:
                        try:
                            temp = float(msg['text'])
                        except:
                            self.bot.sendMessage(chat_id, 'This is not a valid number or STOP. Try again.')
                            return

                    try:
                        r = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/changetemp/', params = {'IDTerr': self.terr['ID'], 'temp': temp})
                        r.raise_for_status()

                    except requests.HTTPError as err:
                        self.bot.sendMessage(chat_id, 'An error happened. Try again.')
                        print err
                        return

                    if temp != 'null':
                        self.bot.sendMessage(chat_id, 'The reference temperature of ' + self.terr['ID'] + ' has been correctly set to %.1f Celsius degrees.'%temp)
                    else:
                        self.bot.sendMessage(chat_id, 'Temperature control has been deactivated.')

                # Conversation about light cycle
                elif self.send2:

                    self.send2 = 0
                    r = re.compile('\d\d:\d\d \d\d:\d\d')

                    if msg['text'] == 'STOP':
                        dawn = 'null'
                        dusk = 'null'

                    elif r.match(msg['text']) != None:
                        dawn = msg['text'].split(' ')[0]
                        dusk = msg['text'].split(' ')[1]

                        # check on the hour feasibility
                        dawn_h = int(dawn.split(':')[0])
                        dawn_m = int(dawn.split(':')[1])
                        dusk_h = int(dusk.split(':')[0])
                        dusk_m = int(dusk.split(':')[1])

                        if dawn_h > 24 or dusk_h > 24 or dawn_m > 59 or dusk_m > 59:
                            self.bot.sendMessage(chat_id, "The times are not feasible. Don't try to fool me.")
                            return

                    else:
                        self.bot.sendMessage(chat_id, 'The format is not correct. Try again.')
                        return

                    try:
                        r = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/changelightcycle/', params = {'IDTerr': self.terr['ID'], 'dawn': dawn, 'dusk': dusk})
                        r.raise_for_status()

                    except requests.HTTPError as err:
                        self.bot.sendMessage(chat_id, 'An error happened. Try again.')
                        print err
                        return

                    if dawn != 'null':
                        self.bot.sendMessage(chat_id, 'The light of ' + self.terr['ID'] + ' will turn on at ' + dawn + ' and will turn off at %s.'%dusk)
                    else:
                        self.bot.sendMessage(chat_id, 'Light cycle control has been deactivated.')


                else:
                    self.bot.sendMessage(chat_id, "I don't understand... try to write in Parseltongue, or write /help.")


    def on_callback_query(self, msg):
        query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')
        query = query_data.split('_')[0]
        terrariumIP = query_data.split('_')[1]
        terrariumport = query_data.split('_')[2]
        URL = 'http://' + terrariumIP + ':' + terrariumport

        if query == 'photo':
            try:
                img = urllib2.urlopen(URL + "static/image1.jpeg")
                localFile = open('photo.jpeg', 'wb')
                localFile.write(img.read())
                localFile.close()
                self.bot.sendPhoto(chat_id, open('photo.jpeg', 'rb'))
            except Exception as err:
                print err
                self.bot.sendMessage(chat_id, 'An error happened. Try again.')

        elif query == 'temp':
            try:
                r = requests.get(URL + 'temperature')
                r.raise_for_status()
                res = (((r.json())['e'])[0])['v']
            except:
                self.bot.sendMessage(chat_id, 'An error happened. Try again.')
                return

            self.bot.sendMessage(chat_id, 'The current temperature is %.1f'%res + ' ' + (((r.json())['e'])[0])['u'])

        elif query == 'hum':
            try:
                r = requests.get(URL + 'humidity')
                r.raise_for_status()
                res = (((r.json())['e'])[0])['v']
                alert = (((r.json())['e'])[1])['v']
            except:
                self.bot.sendMessage(chat_id, 'An error happened. Try again.')
                return

            if alert == 0:
                self.bot.sendMessage(chat_id, 'The current humidity is %.1f'%res + (((r.json())['e'])[0])['u'] + ', and this is fine.')
            elif alert == 1:
                self.bot.sendMessage(chat_id, 'The current humidity is %.1f'%res + (((r.json())['e'])[0])['u'] + ', and this is not okay. I suggest you to fill or move the water bowl.')
            else:
                self.bot.sendMessage(chat_id, 'An error happened. Try again.')

        elif query == 'lock':
            try:
                r = requests.get(URL + 'lock_status')
                r.raise_for_status()
                res = (((r.json())['e'])[0])['v']
            except:
                self.bot.sendMessage(chat_id, 'An error happened. Try again.')
                return

            if res == 'open':
                self.bot.sendMessage(chat_id, 'The terrarium is open.')
            elif res == 'closed':
                self.bot.sendMessage(chat_id, 'The terrarium is closed.')
            else:
                self.bot.sendMessage(chat_id, 'An error happened. Try again.')

class HumidityAlert(threading.Thread):

    def __init__(self, mybot):
        threading.Thread.__init__(self)
        self.mybot = mybot

    def run(self):
        URL_cat = 'http://' + self.mybot.catalogIP + ':' + self.mybot.catalogport + '/terraria'
        r = requests.get(URL_cat)
        terraria = r.json()['terraria']

        for terrarium in terraria:
            URL_terr = 'http://' + terrarium['IP'] + ':' + str(terrarium['port'])
            try:
                r = requests.get(URL_terr + 'humidity')
                r.raise_for_status()
            except requests.HTTPError as err:
                print err
                continue
            alert = (((r.json())['e'])[1])['v']
            if alert == 1:
                try:
                    r = requests.get('http://' + self.mybot.catalogIP + ':' + self.mybot.catalogport + '/user', params = {'ID': terrarium['user']})
                    r.raise_for_status()
                    user = r.json()['user']
                    self.mybot.bot.sendMessage(user['chat_id'], 'Hey, ' + user['nickname'] + '. The humidity of ' + terrarium['ID'] + ' is not correct. I suggest you to move or fill the water bowl.')
                except requests.HTTPError as err:
                    print err
                    continue

        time.sleep(60*15)


if __name__ == '__main__':

    NewBot = MyBot("botconf.txt")
    while 1:
        time.sleep(10)
