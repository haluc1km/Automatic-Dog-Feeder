import imaplib
import email
from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD
import httplib2
import random
import json
import RPi.GPIO as GPIO
import os
import html2text
import re
import time
from time import sleep, strftime
from datetime import datetime

released = False
modeChanged = False
t = time.time()
motoRPin1 = 13
last = 1670514726.3965461
buttonPin = 12  
optionsButton = 18 #need to change
motoRPin2 = 11
enablePin = 15
mode = "Treat"
feedInterval = 28800.0 #8 hours in seconds
FEEDFILE='/home/pi/Documents/FEEDFILE.txt'

def setup():
    global p
    GPIO.cleanup()
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(motoRPin1,GPIO.OUT)   # set pins to OUTPUT mode
    GPIO.setup(motoRPin2,GPIO.OUT)
    GPIO.setup(enablePin,GPIO.OUT)
    GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(optionsButton, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
        
    p = GPIO.PWM(enablePin,1000) # creat PWM and set Frequence to 1KHz
    p.start(0)

def spin_motor_treat(value):
    GPIO.output(motoRPin1,GPIO.HIGH)  # motoRPin1 output HIHG level
    GPIO.output(motoRPin2,GPIO.LOW)
    p.start(100)
    time.sleep(value)
    GPIO.output(motoRPin1,GPIO.LOW)
    GPIO.output(motoRPin2,GPIO.LOW)
    p.stop()
    
PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.
# Create PCF8574 GPIO adapter.
try:
    mcp = PCF8574_GPIO(PCF8574_address)
except:
    try:
        mcp = PCF8574_GPIO(PCF8574A_address)
    except:
        print ('I2C Address Error !')
        exit(1)
# Create LCD, passing in MCP GPIO adapter.
lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)

def get_time_now():     # get system time
    return datetime.now().strftime('    %H:%M:%S')

def spacing(string, output):
    newLine = -1
    newScreen = 0
    i = 0
    while i < len(string):
        if(string[i].isspace()):
            string = string[:i] + "\n" + string[i+1:]
        else:
            for j in range(i, 0, -1):
                if(string[j].isspace()):
                    string = string[:j] + "\n" + string[j+1:]
                    i = j
                    break
        i = i +16
    for l in range(0, len(string), 1):
        if(string[l:l+1] == "\n"):
            newScreen = newScreen +1
            if(newScreen == 2):
                output.append(string[newLine+1:l])
                newLine = l
                newScreen = 0
        if(l+1 == len(string) ):
            output.append(string[newLine+1:len(string)])
    return output

def getJoke():
    # The database where the joke are stored
    NUMDB="https://official-joke-api.appspot.com/random_joke"
    # Doing a HTTP request to get the response (resp) and content (content)
    resp, content = httplib2.Http().request(NUMDB)
    # The content is in the following JSON format and needs to be parsed
    # {u'text': u'Text of joke', u'type' : u'joke, u'number': <number>, u'found': True}
    parsed_content = json.loads(content)
    lcd.setCursor(0,0)
    setup = (parsed_content['setup']) + "\n \n"
    punchline = (parsed_content['punchline'])
    joke_output = []
    joke_output = spacing(setup, joke_output)
    joke_output = spacing(punchline, joke_output)
    for item in joke_output:
        lcd.message(item)
        sleep(3)
        lcd.clear()

def getNumberTrivia():
    # The database where the trivia are stored
    NUMDB="http://numbersapi.com/random/trivia?json"
    # Doing a HTTP request to get the response (resp) and content (content)
    resp, content = httplib2.Http().request(NUMDB)
    # The content is in the following JSON format and needs to be parsed
    # {u'text': u'Text of trivia', u'type' : u'trivia, u'number': <number>, u'found': True}
    parsed_content = json.loads(content)
    lcd.setCursor(0,0)
    trivia_facts = []
    trivia_facts.append("Fact about \n# " + str(parsed_content['number']) + " \n" + "\n")
    trivia = parsed_content['text']
    trivia_facts = spacing(trivia, trivia_facts)

    for item in trivia_facts:
        lcd.message(item)
        sleep(4)
        lcd.clear()

def give_treat(mode):
    global lastFeed
    if mode == "Treat":
        value = 15
    else:
        value = 25
        lastFeed = time.time() - feedInterval + 5
        saveLastFeed()
    random_number = random.randint(1, 5)
    if mode == "Treat":
        if(random_number == 1):
            lcd.message("Someone sent you\na treat Wilson!")
        elif(random_number == 2):
            lcd.message("Woof! Woof! \nIt's treat time!")
        elif(random_number == 3):
            lcd.message("Come get your\nyummy treat bud!")
        elif(random_number == 4):
            lcd.message("Bark! Bark! \nSpecial delivery")
        elif(random_number == 5):
            lcd.message("ohhhhhh Wilson!")
    else:
        lcd.message("Wilson! It's\nfeeding time!")
    spin_motor_treat(value)
    sleep(3)
    
def is_number(string):
    try:
        float(string)
        return True
    except ValueError:
        return False
def destroy():
    lcd.clear()
    mcp.output(3,0)

def display_message():
    mcp.output(3,1)     # turn on LCD backlight
    lcd.begin(16,2)     # set number of LCD lines and columns
    lcd.noAutoscroll()

def read_email():
        mail = imaplib.IMAP4_SSL('imap.zoho.com', 993)
        mail.login('wilsontreats@zohomail.com','dCL2RY7GjhLr')
        mail.select('inbox')
        (retcode, messages) = mail.search(None, 'UNSEEN')
        if retcode == 'OK':
            if len(messages[0].split()) > 0:
                result, data = mail.search(None, 'ALL')
                mail_ids = data[0]
                id_list = mail_ids.split()
                latest_email_id = int(id_list[-1])
                result, data = mail.fetch(str(latest_email_id), '(RFC822)' )

                for response_part in data:
                        result, data = mail.store(str(latest_email_id), '+FLAGS', '\SEEN')
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            email_subject = msg['subject']
                            b = email.message_from_string(str(response_part[1],'utf-8'))
                            body = ""
                            if b.is_multipart():
                                for part in b.walk():
                                    ctype = part.get_content_type()
                                    cdispo = str(part.get('Content-Disposition'))
                                    if ctype == 'text/plain' and 'attachment' not in cdispo:
                                        body = part.get_payload(decode=True)
                                        break
                            if(email_subject == "New submission from Treat"):
                                display_message()
                                give_treat(mode)
                                sleep(3)
                                destroy()
                            if(email_subject == "New submission from Trivia"):
                                display_message()
                                getNumberTrivia()
                                sleep(3)
                                destroy()
                            if(email_subject == "New submission from Joke"):
                                display_message()
                                getJoke()
                                sleep(3)
                                destroy()
                            if(email_subject == "New submission from Time"):
                                try:
                                    global feedInterval
                                    result = re.search('message:\r\n(.*)\r\n\r\n\r\nemail:', body.decode('utf-8'))
                                    if (is_number(result.group(1))) == True:
                                        newTime = float(result.group(1))
                                        feedInterval = (newTime*60*60)
                                except:
                                        print("Not a valid time!")

def saveLastFeed():
    global FEEDFILE
    global lastFeed
    with open(FEEDFILE, 'w') as feedFile:
        feedFile.write(str(lastFeed))
    feedFile.close()

setup()

if os.path.isfile(FEEDFILE):
    with open(FEEDFILE, 'r') as feedFile:
        lastFeed = float(feedFile.read())
        feedFile.close()
else:
    lastFeed = time.time()
    saveLastFeed()

while True:
    if GPIO.input(buttonPin)==GPIO.LOW:
        display_message()
        give_treat(mode)
        sleep(1)
        destroy()
        
    if GPIO.input(optionsButton)==GPIO.LOW:
        while True:
            if GPIO.input(optionsButton)!=GPIO.LOW:
                released = True
                break

        if mode == "Treat" and modeChanged == False:
            display_message()
            lcd.clear()
            lcd.message("1. Feed mode? \n2. Cancel")
            while True:
                if GPIO.input(buttonPin)==GPIO.LOW:
                    mode = "Feed"
                    modeChanged = True
                    lcd.clear()
                    destroy()
                    while True:
                        if GPIO.input(buttonPin)!=GPIO.LOW:
                            break
                    time.sleep(1)
                    break
                if GPIO.input(optionsButton)==GPIO.LOW  and released == True :
                    lcd.clear()
                    destroy()
                    released = False
                    time.sleep(1)
                    break

        if mode == "Feed" and modeChanged == False:
            display_message()
            lcd.clear()
            lcd.message("1. Treat mode? \n2. Cancel")
            while True:
                if GPIO.input(buttonPin)==GPIO.LOW:
                    mode = "Treat"
                    modeChanged = True
                    lcd.clear()
                    destroy()
                    while True:
                        if GPIO.input(buttonPin)!=GPIO.LOW:
                            break
                    time.sleep(1)
                    break
                if GPIO.input(optionsButton)==GPIO.LOW  and released == True:
                    lcd.clear()
                    destroy()
                    released = False
                    time.sleep(1)
                    break
    modeChanged = False

    if (time.time() - t) > 60:
        read_email()
        t = time.time()

    if mode == "Feed":
        if (time.time() - lastFeed) > feedInterval:
            display_message()
            give_treat(mode)
            sleep(3)
            destroy()
            lastFeed = time.time()
            saveLastFeed()

