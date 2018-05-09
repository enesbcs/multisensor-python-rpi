#!/usr/bin/python3
# Multisensor main program: OPI Eye project
# v1.0
import paho.mqtt.client as mqtt
from unit_cputherm_opi import *
import os
import signal
import json
import datetime
import util

#GLOBAL VARS BEGIN
global mqttc
init_ok = False
#GLOBAL VARS END

mqttServer = "127.0.0.1"
tempdelaysec = 60       # seconds to loop

# Sensor settings begin
PIN_FAN       = 6
IDX_FAN       = 1

IDX_OPITMP    = 2
IDX_OPICPU    = 3
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
    global mqttc
    # Clean up on CTRL-C
    print('\r\n' + getTime() + ': Exiting...')
    mqttc.loop_stop()
    mqttc.disconnect()
    sys.exit(0)

def mqttPublish(msg):
    global mqttc, mqttSend
    # Publish to MQTT server
#    print(msg) # DEBUG
    mqttc.publish(mqttSend, msg)

def on_connect(client, userdata, flags, rc):
 global mqttc, mqttReceive
 mqttc.subscribe(mqttReceive,0)

def on_message(mosq, obj, msg):
  global sCPU
  msg2 = msg.payload.decode('utf-8')
  list = []
  try:
   list = json.loads(msg2)
  except Exception as e:
   print("JSON decode error:",e,"'",msg2,"'")
#   print(e)
   list = []
  if (list):
   if (list['idx'] == IDX_FAN): # on/off switch
    if list['nvalue'] == 0:
     sCPU.fancontrol(0)
    else:
     sCPU.fancontrol(1)

# PROGRAM INIT
signal.signal(signal.SIGINT, signalHandler)
print("MQTT connection")
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
try:
 mqttc.connect(mqttServer, 1883)
except:
 print(getTime() + ' MQTT server not found')
 sys.exit(0)

print("Setup CPU thermal sensor")
sCPU   = CPUThermal(PIN_FAN,tempdelaysec,True)

if PIN_FAN != 0:
 msg = domomsg.format(IDX_FAN, sCPU.getfanstate(), motionStates[sCPU.getfanstate()])
 mqttPublish(msg)
mqttc.subscribe(mqttReceive,0)
mqttc.loop_start()
init_ok = True

while init_ok:

  if sCPU.isValueFinal():
    fstate1 = sCPU.getfanstate()
    ctmp = sCPU.readfinalvalue()
    msg = domomsgw.format(IDX_OPITMP,0,str(ctmp[0]),util.rssitodomo(ctmp[2]))
#    print(ctmp)
#    msg = domomsg.format(IDX_PITMP, 0, str(ctmp) )
    mqttPublish(msg)
    msg = domomsgw.format(IDX_OPICPU,0,str(ctmp[1]),util.rssitodomo(ctmp[2]))
    mqttPublish(msg)
    fstate2 = sCPU.getfanstate()
    if (fstate2 != fstate1):
     msg = domomsg.format(IDX_FAN, fstate2, motionStates[fstate2])
     mqttPublish(msg)

  time.sleep(0.5)
