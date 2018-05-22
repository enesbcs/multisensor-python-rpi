#!/usr/bin/python3
# Multisensor main program: Infopanel project
# v1.4
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from unit_cputherm import *
from unit_lht import *
from unit_motion_tri import *
from unit_sound import *
from unit_temp import *
from unit_backlight_onoff import *
import os
import signal
import json
import datetime
import util
import hashlib
import sys

#GLOBAL VARS BEGIN
global mqttc
init_ok = False
lastmot1 = 0
lastmot2 = 0
#GLOBAL VARS END

mqttServer = "192.168.1.10"
tempdelaysec = 80	# seconds to loop

# Sensor settings begin
PIN_TMP      = 22          # Connected to DHT22
IDX_TMP      = 90          # temp sensor IDX

IDX_LHT      = 91          # light sensod Domoticz IDX

PIN_MOTIONP1 = 23          # Connected to HC-SR501 left
PIN_MOTIONP2 = 24          # Connected to HC-SR501 right
PIN_MOTIONR  = 16          # Connected to RCWL-0516

IDX_MOTION1  = 86         # combined motion left idx
IDX_MOTION2  = 87         # combined motion right idx

IDX_PITMP    = 92         # PI CPU temp IDX

IDX_SIREN     = 94        # output siren IDX
IDX_RADIO     = 93        # output radio IDX

PIN_FAN       = 0          # fan is not supported
#IDX_FAN       = 0

PIN_DISP_PWR  = 26        # display on/off IDX
IDX_DISP_PWR  = 95        # relay GPIO pin, that controls  display on/off

NoMotionTime = 900        # seconds to switch off - experimental

TEMP_COMPENSATION = 0
# Sensor settings end

mqttSend      = 'domoticz/in'
mqttReceive   = 'domoticz/out'
motionStates  = [ "Off", "On" ]

domomsg = '{{ "idx": {0}, "nvalue": {1:0.2f}, "svalue": "{2}" }}'
domomsgw = '{{ "idx": {0}, "nvalue": {1:0.2f}, "svalue": "{2}", "RSSI": {3} }}'

def getTime():
    # Save a few key strokes
    return datetime.datetime.now().strftime('%H:%M:%S')
  
def signalHandler(signal, frame):
    global mqttc, sMot#, oBacklight
    # Clean up on CTRL-C
    print('\r\n' + getTime() + ': Exiting...')
    mqttc.loop_stop()
    mqttc.disconnect()
    sMot.signalhandlerRemove()
#    oBacklight.signalhandlerRemove()
    GPIO.cleanup()
    sys.exit(0)
    
def mqttPublish(msg):
    global mqttc, mqttSend
    # Publish to MQTT server
#    print(msg) # DEBUG
    mqttc.publish(mqttSend, msg)
    
def IOHandler(channel):
   global init_ok, sMot, domomsg, lastmove, oBacklight, lastmot1, lastmot2
   if init_ok:
    msg = ""
    msg1 = ""

    if (channel == PIN_MOTIONR) or (channel == PIN_MOTIONP1) or (channel == PIN_MOTIONP2):
#     lv1,lv2 = sMot.getlastvalues()
     nv1,nv2 = sMot.getpinvalues(channel)
     if (nv1 != lastmot1):
      msg = domomsg.format(IDX_MOTION1, nv1, motionStates[nv1])
      lastmot1 = nv1
     if (nv2 != lastmot2):
      msg1 = domomsg.format(IDX_MOTION2, nv2, motionStates[nv2])
      lastmot2 = nv2

    if (msg != "") or (msg1 != ""):
     if msg != "":
      mqttPublish(msg)
     if msg1 != "":
      mqttPublish(msg1)
     if (oBacklight.get_status() == 0) and (nv1+nv2>0):
      lastmove = time.time()
#      oBacklight.set_on()
      msg = domomsg.format(IDX_DISP_PWR, 1, motionStates[1])
      mqttPublish(msg)

def on_connect(client, userdata, flags, rc):
 global mqttc, mqttReceive
 mqttc.subscribe(mqttReceive,0)

def on_message(mosq, obj, msg):
 global oSiren, oBacklight, oRadio, init_ok
 msg2 = msg.payload.decode('utf-8')
 if ('{' in msg2):
  list = []
  try:
   list = json.loads(msg2)
  except Exception as e:
   print("JSON decode error:",e,"'",msg2,"'")
   list = []
  if (list) and (init_ok):
   if (list['idx'] == IDX_SIREN): # select switch
     rlevel = int(list['svalue1'])
     oSiren.play(rlevel)
   if (list['idx'] == IDX_RADIO): # select switch
     oRadio.play(int(list['svalue1']))
   if (list['idx'] == IDX_DISP_PWR): # pwr mode
     pwrmode = int(list['nvalue'])
     if (pwrmode == 0) or (pwrmode == 1):
       oBacklight.set_status(pwrmode)
     else:
      print(list)

# PROGRAM INIT
signal.signal(signal.SIGINT, signalHandler)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
print("MQTT connection")
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
try:
 mqttc.connect(mqttServer, 1883)
except:
 print(getTime() + ' MQTT server not found')
 sys.exit(0)

print("Setup motion sensor")
sMot   = Motion(IOHandler,PIN_MOTIONP1,PIN_MOTIONP2,PIN_MOTIONR)
print("Setup light sensor")
sLight = BH1750(tempdelaysec)
print("Setup temperature sensor")
sTemp  = DHT(PIN_TMP,tempdelaysec)
print("Setup CPU thermal sensor")
sCPU   = CPUThermal(0,tempdelaysec,True) # no vent, only cpu thermal data needed
print("Setup sound outputs")
oSiren = Siren()
oRadio = Radio()
print("Setup backlight control")
msg = domomsg.format(IDX_DISP_PWR, 1, motionStates[1])
mqttPublish(msg)
oBacklight = BacklightControl(PIN_DISP_PWR)

lastmot1, lastmot2 = sMot.getlastvalues()
msg = domomsg.format(IDX_MOTION1, lastmot1, motionStates[lastmot1])
mqttPublish(msg)
msg = domomsg.format(IDX_MOTION2, lastmot2, motionStates[lastmot2])
mqttPublish(msg)
lastmove = time.time()

#mqttc.subscribe(mqttReceive,0)
mqttc.loop_start()
init_ok = True

while init_ok:
  
  if sTemp.isValueFinal():
    atmp, ahum, ahs = sTemp.readfinalvalue()
    atmp -= TEMP_COMPENSATION
    msg = domomsg.format(IDX_TMP, 0, (str(round(atmp,2)) + ";" + str(ahum) + ";" + str(ahs)) )
    mqttPublish(msg)
  else:
    sTemp.readvalue()

  if sLight.isValueFinal():
    alht = sLight.readfinalvalue()
    msg = domomsg.format(IDX_LHT, 0, str(alht) )
    mqttPublish(msg)    
  else:
    sLight.readvalue()

  if sCPU.isValueFinal():
    ctmp = sCPU.readfinalvalue()
    msg = domomsgw.format(IDX_PITMP,0,str(ctmp[0]),util.rssitodomo(ctmp[1]))
    mqttPublish(msg)

#    if ((time.time() - lastmove) > NoMotionTime):
#     print("Display off ", (time.time() - lastmove), " s")
     #oBacklight.set_off()
#     msg = domomsg.format(IDX_DISP_PWR, 0, motionStates[0])
#     mqttPublish(msg)


  time.sleep(0.2)
