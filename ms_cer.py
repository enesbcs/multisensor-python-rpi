#!/usr/bin/python3
# Multisensor main program: Cerberus project
# v1.3
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from unit_cputherm import *
from unit_lht import *
from unit_motion import *
from unit_door import *
from unit_presence import *
from unit_sound import *
from unit_temp import *
from unit_ups import *
import os
import signal
import json
import datetime
import util

#GLOBAL VARS BEGIN
global mqttc
init_ok = False
#GLOBAL VARS END

mqttServer = "localhost"
tempdelaysec = 80	# seconds to loop

# Sensor settings begin
PIN_TMP      = 22          # Connected to DHT22
IDX_TMP      = 22

IDX_LHT      = 23

PIN_MOTION1  = 23          # Connected to HC-SR501
PIN_MOTION2  = 16          # Connected to RCWL-0516

IDX_MOTION_C = 21          # combined motion

IDX_PITMP    = 24

IDX_SIREN     = 25         # output

PIN_FAN       = 0          # fan is not supported in cerberus
#IDX_FAN       = 0

PIN_REED      = 26         # Door reed pin
IDX_REED      = 37

PIN_UPS       = 24         # isPower? UPS Pin
IDX_UPS       = 48
# Sensor settings end

mqttSend      = 'domoticz/in'
mqttReceive   = 'domoticz/out'
motionStates  = [ "Off", "On" ]

domomsg = '{{ "idx": {0}, "nvalue": {1:0.2f}, "svalue": "{2}" }}'
domomsgw = '{{ "idx": {0}, "nvalue": {1:0.2f}, "svalue": "{2}", "RSSI": {3} }}'
domomsgwb = '{{ "idx": {0}, "nvalue": {1:0.2f}, "svalue": "{2}", "RSSI": {3}, "Battery": {4} }}'

def getTime():
    # Save a few key strokes
    return datetime.datetime.now().strftime('%H:%M:%S')
  
def signalHandler(signal, frame):
    global mqttc, sMot, sDor, sUPS
    # Clean up on CTRL-C
    print('\r\n' + getTime() + ': Exiting...')
    mqttc.loop_stop()
    mqttc.disconnect()
    sMot.signalhandlerRemove()
    sDor.signalhandlerRemove()
    sUPS.signalhandlerRemove()
    GPIO.cleanup()
    sys.exit(0)
    
def mqttPublish(msg):
    global mqttc, mqttSend
    # Publish to MQTT server
#    print(msg) # DEBUG
    mqttc.publish(mqttSend, msg)
    
def IOHandler(channel):
   global init_ok, sMot, sDor, domomsg, sUPS, lastupstime
   if init_ok:
    msg = ""
    msg1 = ""

    if (channel == PIN_MOTION1) or (channel == PIN_MOTION2):
     lv = sMot.getlastvalue()
     nv = sMot.getpinvalue(channel)
     if (nv != lv):
       msg = domomsg.format(IDX_MOTION_C, nv, motionStates[nv])

    if (channel == PIN_REED):
     lv = sDor.getlastvalue()
     nv = sDor.getpinvalue(channel)
     if (nv != lv):
       msg = domomsg.format(IDX_REED, nv, motionStates[nv])

    if (channel == PIN_UPS):
     lv = sUPS.getlastvalue()
     nv = sUPS.getpinvalue(channel)
     if (nv != lv) and (time.time() - lastupstime > 30):
       if (nv == 0):
        lastupstime = time.time()
       msg = domomsg.format(IDX_UPS, nv, motionStates[nv])

    if msg != "":   
     mqttPublish(msg)   
    if msg1 != "":   
     mqttPublish(msg1)   

def on_connect(client, userdata, flags, rc):
 global mqttc, mqttReceive
 mqttc.subscribe(mqttReceive,0)

def on_message(mosq, obj, msg):
  global oSiren
  msg2 = msg.payload.decode('utf-8')
  list = []
  try:
   list = json.loads(msg2)
  except Exception as e:
   print("JSON decode error:",e,"'",msg2,"'")
   list = []
  if (list):
   if (list['idx'] == IDX_SIREN): # select switch
     rlevel = int(list['svalue1'])
     oSiren.play(rlevel)

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
sMot   = Motion(IOHandler,PIN_MOTION1,PIN_MOTION2)
print("Setup door sensor")
sDor   = Door(IOHandler,PIN_REED)
print("Setup light sensor")
sLight = BH1750(tempdelaysec)
print("Setup presence detection")
sPres  = Presence(1,300)   # only wifi scans, 5min
print("Setup temperature sensor")
sTemp  = DHT(PIN_TMP,tempdelaysec)
print("Setup CPU thermal sensor")
sCPU   = CPUThermal(0,tempdelaysec,True) # no vent, only cpu thermal data needed
print("Setup sound outputs")
oSiren = Siren()
#oRadio = Radio()
print("Setup UPS battery sensor")
sUPS = UPS(IOHandler,PIN_UPS,0,1,tempdelaysec)

msg = domomsg.format(IDX_MOTION_C, sMot.getlastvalue(), motionStates[sMot.getlastvalue()])
mqttPublish(msg)
msg = domomsg.format(IDX_REED, sDor.getlastvalue(), motionStates[sDor.getlastvalue()])
mqttPublish(msg)
msg = domomsg.format(IDX_UPS, sUPS.getlastvalue(), motionStates[sUPS.getlastvalue()])
mqttPublish(msg)

#mqttc.subscribe(mqttReceive,0)
mqttc.loop_start()
init_ok = True
lastupstime = 0

while init_ok:
  
  if sTemp.isValueFinal():
    atmp, ahum, ahs = sTemp.readfinalvalue()
    msg = domomsg.format(IDX_TMP, 0, (str(atmp) + ";" + str(ahum) + ";" + str(ahs)) )
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
    tvar2 = sUPS.readfinalvalue()
#    print("Battery: ",tvar2[0],"% (",tvar2[1],"V), Power IN:",tvar2[2],"V")
    msg = domomsgwb.format(IDX_PITMP,0,str(ctmp[0]),util.rssitodomo(ctmp[1]),str(tvar2[0]))
    mqttPublish(msg)

  if sPres.isScanTime():
    preslist = sPres.doScan()
    for i in range(len(preslist)):
      msg = domomsg.format(preslist[i],1, motionStates[1])
      mqttPublish(msg)

  time.sleep(0.2)
