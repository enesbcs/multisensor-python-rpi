#!/usr/bin/python3
# Multisensor main program: Cerberus project
# v1.0
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from unit_cputherm import *
from unit_lht import *
from unit_motion import *
from unit_door import *
from unit_presence import *
from unit_sound import *
from unit_temp import *
import os
import signal
import json

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

PIN_FAN       = 0
#IDX_FAN       = 0

PIN_REED      = 26
IDX_REED      = 37
# Sensor settings end

mqttSend      = 'domoticz/in'
mqttReceive   = 'domoticz/out'
motionStates  = [ "Off", "On" ]

domomsg = '{{ "idx": {0}, "nvalue": {1:0.2f}, "svalue": "{2}" }}'


def getTime():
    # Save a few key strokes
    return datetime.now().strftime('%H:%M:%S')
  
def signalHandler(signal, frame):
    global mqttc
    # Clean up on CTRL-C
    print('\r\n' + getTime() + ': Exiting...')
    mqttc.loop_stop()
    mqttc.disconnect()
    sMot.signalhandlerRemove()
    sDor.signalhandlerRemove()
    GPIO.cleanup()
    sys.exit(0)
    
def mqttPublish(msg):
    global mqttc 
    # Publish to MQTT server
#    print(msg) # DEBUG
    mqttc.publish(mqttSend, msg)
    
def IOHandler(channel):
   global init_ok, sMot, sDor, domomsg
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

    if msg != "":   
     mqttPublish(msg)   
    if msg1 != "":   
     mqttPublish(msg1)   
     
def on_message(mosq, obj, msg):
  global oSiren
  msg2 = msg.payload.decode('utf-8')
  list = []
  try:
   list = json.loads(msg2)
  except Exception as e:
   print(e)
   list = []
  if (list):
   if (list['idx'] == IDX_SIREN): # select switch
     oSiren.play(int(list['svalue1']))
     
# PROGRAM INIT
signal.signal(signal.SIGINT, signalHandler)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
print("MQTT connection")
mqttc = mqtt.Client()
mqttc.on_message = on_message
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
sCPU   = CPUThermal(0,tempdelaysec) # no vent, only cpu thermal data needed
print("Setup sound outputs")
oSiren = Siren()
#oRadio = Radio()

msg = domomsg.format(IDX_MOTION_C, sMot.getlastvalue(), motionStates[sMot.getlastvalue()])
mqttPublish(msg)
msg = domomsg.format(IDX_REED, sDor.getlastvalue(), motionStates[sDor.getlastvalue()])
mqttPublish(msg)
mqttc.subscribe(mqttReceive,0)
mqttc.loop_start()
init_ok = True
     
while init_ok:
  
  if sTemp.isValueFinal():
    atmp, ahum = sTemp.readfinalvalue()
    msg = domomsg.format(IDX_TMP, 0, (str(atmp) + ";" + str(ahum) + ";1") )
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
    msg = domomsg.format(IDX_PITMP, 0, str(ctmp) )
    mqttPublish(msg)

  if sPres.isScanTime():
    preslist = sPres.doScan()
    for i in range(len(preslist)):
      msg = domomsg.format(preslist[i],1, motionStates[1])
      mqttPublish(msg)

  time.sleep(0.2)
