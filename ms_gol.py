#!/usr/bin/python3
# Multisensor main program: Goliath project
# v1.3
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from unit_cputherm import *
from unit_flame import *
from unit_lht import *
from unit_motion import *
from unit_mq import *
#from unit_presence import *
from unit_sound import *
from unit_temp import *
import os
import signal
import json
import datetime
import util

#GLOBAL VARS BEGIN
global mqttc
init_ok = False
#GLOBAL VARS END

mqttServer = "192.168.2.100"
tempdelaysec = 80	# seconds to loop

# Sensor settings begin
PIN_TMP      = 22          # Connected to DHT22
IDX_TMP      = 12

IDX_LHT      = 13

PIN_MOTION1  = 23          # Connected to HC-SR501
PIN_MOTION2  = 16          # Connected to RCWL-0516

IDX_MOTION_C = 14         # combined motion

IDX_PITMP    = 19

PIN_FLAME     = 27
IDX_FLAME_PIN = 16
IDX_FLAME_VAL = 26 

PIN_SMOKE     = 17
IDX_SMOKE_PIN = 15
IDX_SMOKE_VAL = 30

IDX_SIREN     = 27         # output
IDX_RADIO     = 38         # output
IDX_TVH       = 31        # process start/stop

PIN_FAN       = 12
IDX_FAN       = 32
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
    global mqttc, sFlame, sSmoke, sMot
    # Clean up on CTRL-C
    print('\r\n' + getTime() + ': Exiting...')
    mqttc.loop_stop()
    mqttc.disconnect()
    sFlame.signalhandlerRemove()
    sSmoke.signalhandlerRemove()
    sMot.signalhandlerRemove()
    GPIO.cleanup()
    sys.exit(0)
    
def mqttPublish(msg):
    global mqttc, mqttSend
    # Publish to MQTT server
#    print(msg) # DEBUG
    mqttc.publish(mqttSend, msg)
    
def IOHandler(channel):
   global init_ok, sFlame, sSmoke, sMot, domomsg
   global lastsmoketime, lastflametime
   if init_ok:
    msg = ""
    msg1 = ""

    if (channel == PIN_MOTION1) or (channel == PIN_MOTION2):
     lv = sMot.getlastvalue()
     nv = sMot.getpinvalue(channel)
     if (nv != lv):
       msg = domomsg.format(IDX_MOTION_C, nv, motionStates[nv])

    if (channel == PIN_FLAME):
     lv = sFlame.getlastvalue()
     nv = sFlame.getpinvalue(channel)
     if (nv != lv) and (time.time() - lastflametime > 30):
       if (nv == 1):
        lastflametime = time.time()
       msg = domomsg.format(IDX_FLAME_PIN, nv, motionStates[nv])
       msg1 = domomsg.format(IDX_FLAME_VAL, 0, sFlame.getlastnumvalue() )

    if (channel == PIN_SMOKE):
     lv = sSmoke.getlastvalue()
     nv = sSmoke.getpinvalue(channel)
     if (nv != lv) and (time.time() - lastsmoketime > 30):
       if (nv == 1):
        lastsmoketime = time.time()
       msg = domomsg.format(IDX_SMOKE_PIN, nv, motionStates[nv])
       msg1 = domomsg.format(IDX_SMOKE_VAL, 0, sSmoke.getlastnumvalue() )

    if msg != "":   
     mqttPublish(msg)   
    if msg1 != "":   
     mqttPublish(msg1)   

def on_connect(client, userdata, flags, rc):
 global mqttc, mqttReceive
 mqttc.subscribe(mqttReceive,0)

def on_message(mosq, obj, msg):
  global oSiren, oRadio, sCPU
  msg2 = msg.payload.decode('utf-8')
  list = []
  try:
   list = json.loads(msg2)
  except Exception as e:
   print("JSON decode error:",e,"'",msg2,"'")
#   print(e)
   list = []
  if (list):
   if (list['idx'] == IDX_SIREN): # select switch
     oSiren.play(int(list['svalue1']))
   if (list['idx'] == IDX_RADIO): # select switch
     oRadio.play(int(list['svalue1']))
   if (list['idx'] == IDX_TVH): # on/off switch
    if list['nvalue'] == 0:
     os.system("sudo /etc/init.d/tvheadend stop")
    else:
     os.system("sudo /etc/init.d/tvheadend start")
   if (list['idx'] == IDX_FAN): # on/off switch
    if list['nvalue'] == 0:
     sCPU.fancontrol(0)
    else:
     sCPU.fancontrol(1)
     
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
print("Setup smoke sensor")
sSmoke = MQ(IOHandler,PIN_SMOKE,0,tempdelaysec)
print("Setup flame sensor")
sFlame = Flame(IOHandler,PIN_FLAME,1,tempdelaysec)
print("Setup light sensor")
sLight = BH1750(tempdelaysec)
#print("Setup presence detection")
#sPres  = Presence(2,300)
print("Setup temperature sensor")
sTemp  = DHT(PIN_TMP,tempdelaysec)
print("Setup CPU thermal sensor")
sCPU   = CPUThermal(PIN_FAN,tempdelaysec,True)
print("Setup sound outputs")
oSiren = Siren()
oRadio = Radio()
os.system("sudo /etc/init.d/tvheadend stop") # stop tvheadend if running

msg = domomsg.format(IDX_MOTION_C, sMot.getlastvalue(), motionStates[sMot.getlastvalue()])
mqttPublish(msg)
msg = domomsg.format(IDX_FLAME_PIN, sFlame.getlastvalue(), motionStates[sFlame.getlastvalue()])
mqttPublish(msg)
msg = domomsg.format(IDX_SMOKE_PIN, sSmoke.getlastvalue(), motionStates[sSmoke.getlastvalue()])
mqttPublish(msg)
if PIN_FAN != 0:
 msg = domomsg.format(IDX_FAN, sCPU.getfanstate(), motionStates[sCPU.getfanstate()])
 mqttPublish(msg)
mqttc.subscribe(mqttReceive,0)
mqttc.loop_start()
init_ok = True
lastsmoketime = 0
lastflametime = 0

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
    fstate1 = sCPU.getfanstate()
    ctmp = sCPU.readfinalvalue()
    msg = domomsgw.format(IDX_PITMP,0,str(ctmp[0]),util.rssitodomo(ctmp[1]))
#    msg = domomsg.format(IDX_PITMP, 0, str(ctmp) )
    mqttPublish(msg)
    fstate2 = sCPU.getfanstate()
    if (fstate2 != fstate1):
     msg = domomsg.format(IDX_FAN, fstate2, motionStates[fstate2])
     mqttPublish(msg)

  if sSmoke.isValueFinal():
    tvar = sSmoke.readfinalvalue()
    msg = domomsg.format(IDX_SMOKE_VAL, 0, str(tvar) )
    mqttPublish(msg)    

  if sFlame.isValueFinal():
    tvar = sFlame.readfinalvalue()
    msg = domomsg.format(IDX_FLAME_VAL, 0, str(tvar) )
    mqttPublish(msg)    

#  if sPres.isScanTime():
#    preslist = sPres.doScan()        
#    for i in range(len(preslist)):
#      msg = domomsg.format(preslist[i],1, motionStates[1])
#      mqttPublish(msg)

  sSmoke.CalibrateSometime()
  sFlame.CalibrateSometime()
  time.sleep(0.2)
