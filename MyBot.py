import telepot
import time
from telepot.loop import MessageLoop
import telepot.api
import requests
import json
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import re
import threading
import urllib3
import urllib2

class MyBot:

    def __init__(self, conf_file):

        file = open(conf_file, 'r')
        dict = json.loads(file.read())
        file.close()

        # Variables that keep track of a conversation
        self.user_states = [] # list of dictionaries with {'user': chat_id, 'state': temp|light, 'terr': terr_id}

        self.token = dict['token']
        self.catalogIP = dict['catalog_IP']
        self.catalogport = str(dict['catalog_port'])
        self.bot = telepot.Bot(token=str(self.token))

        MessageLoop(self.bot, {'chat': self.on_chat_message, 'callback_query': self.on_callback_query}).run_as_thread()

    def on_chat_message(self, msg):

        content_type, chat_type, chat_id = telepot.glance(msg)

        if content_type == 'text':

            name = msg["from"]["first_name"]
            command = msg['text']

            if command == '/start':
                self.bot.sendMessage(chat_id, "Hello " + name +
                                    "! I'm your SPYThon bot. Please register yourself with /registermyself to get started.")

            elif command == '/help':
                self.bot.sendMessage(chat_id, """First you can register with: /registermyself. \n Then you can use: /registerterrarium terrariumID password to become the only owner of the terrarium..\n
                 Then you can check how your reptile is doing by: /check terrariumID.\n If you want to set the temperature control just type:
                 /temperature terrariumID, and if you wish to set the dawn and dusk hours of your terrarium type:
                 /light terrariumID""")

            elif command == '/registermyself':         # Register the speaker as a user

                payload = {'nickname':name, 'ID': chat_id}
                URL = 'http://' + self.catalogIP + ':' + self.catalogport + '/add_user'
                try:
                    r = requests.post(URL, data = json.dumps(payload))
                    r.raise_for_status()
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again.')
                    print err
                    return

                self.bot.sendMessage(chat_id, "Congratulations " + name +
                                    "! You have been registered. You can now connect to your reptile.")

            elif command == '/deletemyself':

                URL = 'http://' + self.catalogIP + ':' + self.catalogport + '/delete_user'
                try:
                    r = requests.get(URL, params = {'UserID': chat_id})
                    r.raise_for_status()
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again.')
                    print err
                    return

                self.bot.sendMessage(chat_id, "Hey " + name +
                                    "! It's sad to see you leave. Come back soon!")


            elif command.startswith('/registerterrarium'):  # Associate a terrarium (identified by its ID)
                                                            # to the speaker (identified by the chat_id).
                                                            # If the speaker or the terrarium are not registered, raise an error.

                params_bot = command.split(' ')

                if len(params_bot) < 3:
                    self.bot.sendMessage(chat_id, 'The correct syntax is: /registerterrarium terrariumID password')
                    return

                try:
                    r = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/user/', params = {'ID': chat_id})
                    r.raise_for_status()
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'Please register yourself first.')
                    return

                payload = {'IDTerr':params_bot[1], 'IDUs': chat_id, 'pws': params_bot[2]}
                URL = 'http://' + self.catalogIP + ':' + self.catalogport + '/associate/'
                try:
                    r = requests.get(URL, params = payload)
                    r.raise_for_status()
                except requests.HTTPError as err:
                    if r.status_code == 401:
                        self.bot.sendMessage(chat_id, 'Password is not correct.')
                    else:
                        self.bot.sendMessage(chat_id, 'An error happened. Try again. (syntax is: /registerterrarium terrariumID password)')
                    return

                self.bot.sendMessage(chat_id, "Congratulations " + name +
                                    "! The terrarium " + params_bot[1] + " has been associated to you. Only you will have access to the terrarium.")

            elif command.startswith('/check'):

                params_bot = command.split(' ')

                if len(params_bot) < 2:
                    self.bot.sendMessage(chat_id, 'Correct syntax is: /check terrariumID')
                    return

                try:
                    r1 = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/terrarium/', params = {'ID': params_bot[1]})
                    r1.raise_for_status()
                    terr = r1.json()['terrarium']
                    if terr['user'] != str(chat_id):
                        self.bot.sendMessage(chat_id, "You can't check the terrarium. Please register and associate yourself to the terrarium.")
                        return
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again and check the connection of the terrarium. (Correct syntax is: /check terrariumID)')
                    return


                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                     [InlineKeyboardButton(text='Photo', callback_data='photo_' + terr['IP'] + '_' + str(terr['port'])),
                     InlineKeyboardButton(text='Temperature', callback_data='temp_' + terr['IP'] + '_' + str(terr['port']))],
                     [InlineKeyboardButton(text='Humidity', callback_data='hum_' + terr['IP'] + '_' + str(terr['port'])),
                     InlineKeyboardButton(text='Lock Status', callback_data='lock_' + terr['IP'] + '_' + str(terr['port']))]])

                msg = self.bot.sendMessage(chat_id, 'What do you want to see?', reply_markup=keyboard)

            elif command.startswith('/temperature'):
                params_bot = command.split(' ')

                if len(params_bot) < 2:
                    self.bot.sendMessage(chat_id, 'Correct syntax is: /temperature terrariumID')
                    return

                try:
                    r1 = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/terrarium/', params = {'ID': params_bot[1]})
                    r1.raise_for_status()
                    terr = r1.json()['terrarium']
                    if terr['user'] != str(chat_id):
                        self.bot.sendMessage(chat_id, "You can't control the terrarium. Please associate to the terrarium.")
                        return
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again and check the connection of the terrarium. (syntax is: /temperature terrariumID)')
                    return

                self.user_states.append({'user': chat_id, 'state': 'temp', 'terr': terr['ID']})
                self.bot.sendMessage(chat_id, 'Please type the reference daytime temperature or type STOP to deactivate the control.')

            elif command.startswith('/light'):
                params_bot = command.split(' ')

                if len(params_bot) < 2:
                    self.bot.sendMessage(chat_id, 'Correct syntax is: /light terrariumID')
                    return

                try:
                    r1 = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/terrarium/', params = {'ID': params_bot[1]})
                    r1.raise_for_status()
                    terr = r1.json()['terrarium']
                    if terr['user'] != str(chat_id):
                        self.bot.sendMessage(chat_id, "You can't control the terrarium. Please associate to the terrarium.")
                        return
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again and check the connection of the terrarium. (syntax is: /light terrariumID)')
                    return

                self.user_states.append({'user': chat_id, 'state': 'light', 'terr': terr['ID']})
                self.bot.sendMessage(chat_id, 'Please type the times in which you want the light to turn on and off (HH:MM) or type STOP to deactivate the control.')

            else:

                send1 = 0
                send2 = 0

                # check if the user is engaged in a conversation

                for state in self.user_states:
                    if state['user'] == chat_id and state['state'] == 'temp':
                        send1 = 1
                        break

                    elif state['user'] == chat_id and state['state'] == 'light':
                        send2 = 1
                        break

                # Conversation about reference temperature
                if send1:

                    if msg['text'] == 'STOP':
                        temp = 'null'
                    else:
                        try:
                            temp = float(msg['text'])
                        except:
                            self.bot.sendMessage(chat_id, 'This is not a valid number or STOP. Try again.')
                            self.user_states.remove(state)
                            return

                    try:
                        r = requests.get('http://' + self.catalogIP + ':' + str(self.catalogport) + '/changetemp/', params = {'IDTerr': state['terr'], 'temp': temp})
                        r.raise_for_status()

                    except requests.HTTPError as err:
                        self.bot.sendMessage(chat_id, 'An error happened. Try again and check the connection of the temperature control.')
                        self.user_states.remove(state)
                        return

                    if temp != 'null':
                        self.bot.sendMessage(chat_id, 'The reference temperature of ' + state['terr'] + ' has been correctly set to %.1f Celsius degrees.'%temp)
                    else:
                        self.bot.sendMessage(chat_id, 'Temperature control has been deactivated.')

                    self.user_states.remove(state)

                # Conversation about light cycle
                elif send2:

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
                            self.user_states.remove(state)
                            return

                    else:
                        self.bot.sendMessage(chat_id, 'The format is not correct. Try again.')
                        self.user_states.remove(state)
                        return

                    try:
                        r = requests.get('http://' + self.catalogIP + ':' + self.catalogport + '/changelightcycle/', params = {'IDTerr': state['terr'], 'dawn': dawn, 'dusk': dusk})
                        r.raise_for_status()

                    except requests.HTTPError as err:
                        self.bot.sendMessage(chat_id, 'An error happened. Try again and check the connection of the light control.')
                        self.user_states.remove(state)
                        print err
                        return

                    if dawn != 'null':
                        self.bot.sendMessage(chat_id, 'The light of ' + state['terr'] + ' will turn on at ' + dawn + ' and will turn off at %s.'%dusk)
                    else:
                        self.bot.sendMessage(chat_id, 'Light cycle control has been deactivated.')

                    self.user_states.remove(state)

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
                img = urllib2.urlopen(URL + "/static/image1.jpeg")
                localFile = open('photo.jpeg', 'wb')
                localFile.write(img.read())
                localFile.close()
                self.bot.sendPhoto(chat_id, open('photo.jpeg', 'rb'))
            except Exception as err:
                print err
                self.bot.sendMessage(chat_id, 'An error happened. Try again.')

        elif query == 'temp':
            try:
                r = requests.get(URL + '/temperature')
                r.raise_for_status()
                res = (((r.json())['e'])[0])['v']
            except:
                self.bot.sendMessage(chat_id, 'An error happened. Try again.')
                return

            self.bot.sendMessage(chat_id, 'The current temperature is %.1f'%res + ' ' + (((r.json())['e'])[0])['u'])

        elif query == 'hum':
            try:
                r = requests.get(URL + '/humidity')
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
                r = requests.get(URL + '/lock_status')
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
        while True:

            URL_cat = 'http://' + self.mybot.catalogIP + ':' + self.mybot.catalogport + '/terraria'
            r = requests.get(URL_cat)
            terraria = r.json()['terraria']

            for terrarium in terraria:
                if terrarium['user'] != None:
                    URL_terr = 'http://' + terrarium['IP'] + ':' + str(terrarium['port'])
                    try:
                        r = requests.get(URL_terr + '/humidity')
                        r.raise_for_status()
                    except requests.HTTPError as err:
                        #print err
                        continue
                    alert = (((r.json())['e'])[1])['v']
                    if alert == 1:
                        try:
                            #print 'Sending humidity alert'
                            r = requests.get('https://api.telegram.org/bot' + self.mybot.token + '/sendMessage?chat_id='+ terrarium['user'] + '&text=' + 'Hey, the humidity of ' + terrarium['ID'] + ' is not correct. I suggest you to move or fill the water bowl.')
                            r.raise_for_status()
                        except requests.HTTPError as err:
                            print err

            time.sleep(15*60)


if __name__ == '__main__':

    NewBot = MyBot("botconf.txt")

    # Thread to alert users for incorrect value of humidity
    hum_alert = HumidityAlert(NewBot)
    hum_alert.start()

    while 1:
        time.sleep(10)
