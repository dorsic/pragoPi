'''
Controlling the Pragotron wall watch via pins 16, 18 (GPIO 23 and 24) using Cron Minute events.

'''
APP_VERSION = "0.2.0"

import os
import time
import datetime
import json
import RPi.GPIO as GPIO
from flask import Flask, render_template, request
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)

def doImpulse():
    global clock
    clock.impulse(1.5)

class Pragotron(object):

    # Create a dictionary called pins to store the pin number, name, and pin state:
    pins = {
        23 : {'name' : 'GPIO 23', 'state' : GPIO.LOW },
        24 : {'name' : 'GPIO 24', 'state' : GPIO.LOW }
    }

    scheduler = BackgroundScheduler()

    lastImpulseStatus = { 'utctimestamp': None, 'impulseVoltage': 0, 'displayedTime': '' }
    statusFileName = None

    def __init__(self, statusFileName):
        self.statusFileName = statusFileName
        GPIO.setmode(GPIO.BCM)
        # Set each pin as an output and make it low:
        for pin in self.pins:
            print('Initializing pin ' + str(pin))
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        self.scheduler.add_job(doImpulse, trigger='cron', minute='*', id='minuter')
         
        if os.path.isfile(self.statusFileName):
            self.readStatus()
            self.setTime(self.lastImpulseStatus['displayedTime'])

        self.scheduler.start()

    def strToIntTime(self, timeStr):
        if ':' in timeStr:
            (h, m) = timeStr.split(':')
            return ((int(h)%12) * 100) + (int(m) % 60)
        if timeStr:
            return int(timeStr)

    def intTimeToStr(self, intTime):
        return "%02d" % (intTime//100,) + ':' + "%02d" % (intTime % 100,)

    def incTime(self):                
        intTime = self.strToIntTime(self.lastImpulseStatus['displayedTime'])
        if not intTime is None:
            intTime = intTime + 1
            intTime = intTime + 100-60 if intTime % 100 > 59 else intTime
            intTime = intTime - 1200 if intTime > 1159 else intTime
            self.lastImpulseStatus['displayedTime'] = self.intTimeToStr(intTime)

    def writeStatus(self):
        with open(self.statusFileName, 'w') as f:
            json.dump(self.lastImpulseStatus, f)

    def readStatus(self):
        with open(self.statusFileName, 'r') as f:
            self.lastImpulseStatus = json.load(f)

    def impulse(self, length = 1.5):
        print('Generating a ' + ('NEGATIVE' if self.lastImpulseStatus['impulseVoltage'] else 'POSITIVE') + ' impulse.')
        pin = list(self.pins.keys())[0] if self.lastImpulseStatus['impulseVoltage'] else list(self.pins.keys())[1]
        print('Setting pin ' + str(pin) + ' HIGH')
        self.pins[pin]['state'] = GPIO.HIGH
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(length)
        self.pins[pin]['state'] = GPIO.LOW
        GPIO.output(pin, GPIO.LOW)
        self.lastImpulseStatus['utctimestamp'] = str(datetime.datetime.utcnow())
        self.lastImpulseStatus['impulseVoltage'] = (self.lastImpulseStatus['impulseVoltage'] + 1) % 2
        self.incTime()
        self.writeStatus()
        print('Impulse done.')

    def setTime(self, displayedTime):
        # disable schedule
        if not displayedTime:
            print("Unknown displayed time. Cannot set time.")
            return

        self.scheduler.pause_job('minuter')

        t = datetime.datetime.now()
        tnow = (t.hour%12) * 100 + t.minute
        cdt = self.strToIntTime(displayedTime)
        self.lastImpulseStatus['displayedTime'] = self.intTimeToStr(cdt)

        while cdt > tnow:
            print('Setting time, ' + str(cdt)  + ' > ' + str(tnow))
            self.impulse(0.3)
            time.sleep(0.3)            
            cdt = self.strToIntTime(self.lastImpulseStatus['displayedTime'])
            t = datetime.datetime.now()
            tnow = (t.hour%12) * 100 + t.minute

        while cdt < tnow:
            print('Setting time, ' + str(cdt) + ' < ' + str(tnow))
            self.impulse(0.3)
            time.sleep(0.3)            
            cdt = self.strToIntTime(self.lastImpulseStatus['displayedTime'])
            t = datetime.datetime.now()
            tnow = (t.hour%12) * 100 + t.minute

        print('Done in at ' + str(datetime.datetime.now()) + '. Resuming scheduler.')
        # enable scheduler
        self.scheduler.resume_job('minuter')

    def shutdown(self):
        self.scheduler.shutdown(wait=False)
        GPIO.cleanup()

def getTemplateData():
    global clock
    tnow = datetime.datetime.now()
    utcnow = datetime.datetime.utcnow()
    #tstr = tnow.isoformat(sep=' ', timespec='seconds')
    #utcstr = utcnow.isoformat(sep=' ', timespec='seconds')

    templateData = {
        'appVersion': APP_VERSION,
        'timestamp' : str(tnow),
        'utcTimestamp': str(utcnow),
        'lastImpulseStatus': clock.lastImpulseStatus,
    }
    return templateData


@app.route("/")
def main():
    templateData = getTemplateData()
    # Pass the template data into the template main.html and return it to the user
    return render_template('main.html', **templateData)
    
@app.route("/impulse")
def impulse():
    global clock
    clock.impulse(1.5)
    templateData = getTemplateData()
    return render_template('main.html', **templateData)    

@app.route("/setTime/<displayedTime>")
def setTime(displayedTime):
    global clock
    global scheduler
    clock.setTime(displayedTime)

    templateData = getTemplateData()
    return render_template('main.html', **templateData)

def cleanup():
    try:
        global clock
        clock.shutdown()
    except Exception:
        pass

atexit.register(cleanup)

if __name__ == "__main__":
    clock = Pragotron('/home/pi/pragoPi/clockStatus.conf')
    app.run(host='0.0.0.0', port=80, debug=False)
