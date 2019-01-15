import telepot
import time
from telepot.loop import MessageLoop
import requests
import json
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import re
import urllib2

conf_file = "botconf.txt"

class MyBot:

    def __init__(self):

        file = open(conf_file, 'r')
        dict = json.loads(file.read())
        file.close()
        self.send1 = 0
        self.send2 = 0
        self.terr = None
        self.token = dict['token']
        self.catalogIP = dict['catalog_IP']
        self.cnt = 0
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
                self.bot.sendMessage(chat_id, """First you can register with: /registermyself. \n When you have your ID, you can use: /registerterrarium <myID> <terrariumID> to become the only owner of the terrarium..\n
                 Then you can check how your reptile is doing by: /check <myID> <terrariumID>.\n If you want to set the temperature control just type:
                 /controltemperature <myID> <terrariumID>, and if you wish to set the dawn and dusk hours of your terrarium type:
                 /controllightcycle <myID> <terrariumID>""")

            elif command == '/registermyself':         # Register the speaker as a user
                ID = 'user' + str(self.cnt)
                self.cnt += 1
                payload = {'ID':ID, 'nickname':name}
                URL = 'http://' + self.catalogIP + ':8080/add_user'
                try:
                    r = requests.post(URL, data = json.dumps(payload))
                    r.raise_for_status()
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again.')
                    return

                self.bot.sendMessage(chat_id, "Congratulations " + name +
                                    "! You have been registered with ID: " + ID +
                                    ". Please remember it and use it to identify yourself.")



            elif command.startswith('/registerterrarium'):  # Associate a terrarium (identified by its ID)
                                                            # to the speaker, who must give his/her ID.
                                                            # If the speaker or the terrarium are not registered, raise an error.

                params_bot = command.split(' ')[1:]
                if len(params_bot) < 2:
                    self.bot.sendMessage(chat_id, '/registerterrarium <myID> <terrariumID>')
                    return

                payload = {'IDTerr':params_bot[1], 'IDUs':params_bot[0]}
                URL = 'http://' + self.catalogIP + ':8080/associate/'
                try:
                    r = requests.get(URL, params = payload)
                    r.raise_for_status()
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again. (/registerterrarium <myID> <terrariumID>)')
                    return

                self.bot.sendMessage(chat_id, "Congratulations " + name +
                                    "! The terrarium " + params_bot[1] + " has been associated to user " + params_bot[0] +
                                    ". Only this user has the right to access to the terrarium.")

            elif command.startswith('/check'):
                params_bot = command.split()[1:]

                if len(params_bot) < 2:
                    self.bot.sendMessage(chat_id, '/check <myID> <terrariumID>')
                    return

                try:
                    r1 = requests.get('http://' + self.catalogIP + ':8080/terrarium/', params = {'ID': params_bot[1]})
                    r1.raise_for_status()
                    terr = r1.json()
                    if terr['user'] != params_bot[0]:
                        self.bot.sendMessage(chat_id, "This user can't check the terrarium. Please associate the user to the terrarium.")
                        return
                    r2 = requests.get('http://' + self.catalogIP + ':8080/user/', params = {'ID': params_bot[0]})
                    r2.raise_for_status()
                    user = r2.json()
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again. (/check <myID> <terrariumID>)')
                    return


                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                     [InlineKeyboardButton(text='Photo', callback_data='photo_' + terr['IP']),
                     InlineKeyboardButton(text='Temperature', callback_data='temp_' + terr['IP'])],
                     [InlineKeyboardButton(text='Humidity', callback_data='hum_' + terr['IP']),
                     InlineKeyboardButton(text='Lock Status', callback_data='lock_' + terr['IP'])]])

                self.bot.sendMessage(chat_id, 'What do you want to see?', reply_markup=keyboard)

            elif command.startswith('/controltemperature'):
                params_bot = command.split()[1:]

                if len(params_bot) < 2:
                    self.bot.sendMessage(chat_id, '/controltemperature <myID> <terrariumID>')
                    return

                try:
                    r1 = requests.get('http://' + self.catalogIP + ':8080/terrarium/', params = {'ID': params_bot[1]})
                    r1.raise_for_status()
                    self.terr = r1.json()
                    if self.terr['user'] != params_bot[0]:
                        self.bot.sendMessage(chat_id, "This user can't control the terrarium. Please associate the user to the terrarium.")
                        return
                    r2 = requests.get('http://' + self.catalogIP + ':8080/user/', params = {'ID': params_bot[0]})
                    r2.raise_for_status()
                    user = r2.json()
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again. (/controltemperature <myID> <terrariumID>)')
                    return

                self.send1 = self.bot.sendMessage(chat_id, 'Please type the reference temperature or type STOP to deactivate the control.')

            elif command.startswith('/controllightcycle'):
                params_bot = command.split()[1:]

                if len(params_bot) < 2:
                    self.bot.sendMessage(chat_id, '/controllightcycle <myID> <terrariumID>')
                    return

                try:
                    r1 = requests.get('http://' + self.catalogIP + ':8080/terrarium/', params = {'ID': params_bot[1]})
                    r1.raise_for_status()
                    self.terr = r1.json()
                    if self.terr['user'] != params_bot[0]:
                        self.bot.sendMessage(chat_id, "This user can't control the terrarium. Please associate the user to the terrarium.")
                        return
                    r2 = requests.get('http://' + self.catalogIP + ':8080/user/', params = {'ID': params_bot[0]})
                    r2.raise_for_status()
                    user = r2.json()
                except requests.HTTPError as err:
                    self.bot.sendMessage(chat_id, 'An error happened. Try again. (/controllightcycle <myID> <terrariumID>)')
                    return

                self.send2 = self.bot.sendMessage(chat_id, 'Please type the times in which you want the light to turn on and off (HH:MM) or type STOP to deactivate the control.')

            else:

                if self.send1:

                    self.send1 = 0
                    if msg['text'].isdigit():
                        temp = float(msg['text'])
                    elif msg['text'] == 'STOP':
                        temp = 'null'
                    else:
                        self.bot.sendMessage(chat_id, 'This is not a valid number or STOP. Try again.')
                        return

                    try:
                        r = requests.get('http://' + self.catalogIP + ':8080/changetemp/', params = {'IDTerr': self.terr['ID'], 'temp': temp})
                        r.raise_for_status()

                    except requests.HTTPError as err:
                        self.bot.sendMessage(chat_id, 'An error happened. Try again.')
                        return

                    if temp != 'null':
                        self.bot.sendMessage(chat_id, 'The reference temperature of ' + self.terr['ID'] + ' has been correctly set to %.1f Celsius degrees.'%temp)
                    else:
                        self.bot.sendMessage(chat_id, 'Temperature control has been deactivated.')

                elif self.send2:

                    self.send2 = 0
                    r = re.compile('\d\d:\d\d \d\d:\d\d')
                    if msg['text'] == 'STOP':
                        dawn = 'null'
                        dusk = 'null'
                    elif r.match(msg['text']) != None:
                        dawn = msg['text'].split(' ')[0]
                        dusk = msg['text'].split(' ')[1]
                    else:
                        self.bot.sendMessage(chat_id, 'The format is not correct. Try again.')
                        return

                    try:
                        r = requests.get('http://' + self.catalogIP + ':8080/changelightcycle/', params = {'IDTerr': self.terr['ID'], 'dawn': dawn, 'dusk': dusk})
                        r.raise_for_status()

                    except requests.HTTPError as err:
                        self.bot.sendMessage(chat_id, 'An error happened. Try again.')
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
        URL = 'http://' + terrariumIP + ':8080/'
        #URL = 'http://localhost:8081/'

        if query == 'photo':
            try:
                img = urllib2.urlopen(URL + "static/image1.jpeg")
                localFile = open('photo.jpeg', 'wb')
                localFile.write(img.read())
                localFile.close()
                self.bot.sendPhoto(chat_id, open('photo.jpeg', 'rb'))
                #self.bot.sendPhoto(chat_id, 'http://www.nationalgeographic.it/images/2017/03/27/111938081-4a9bf11d-61ac-4afe-81f3-c37967664a68.jpg')
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
                self.bot.sendMessage(chat_id, 'The current humidity is %.1f'%res + (((r.json())['e'])[0])['u'] + ', and this is not okay. You should take action.')
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


if __name__ == '__main__':

    NewBot = MyBot()
    while 1:
        time.sleep(10)
