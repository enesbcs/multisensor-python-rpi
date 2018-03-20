#!/usr/bin/python3
# Multisensor main program: Cerberus project
# v1.4
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
from unit_wiegand import *
import os
import signal
import json
import datetime
import util
import hashlib

#GLOBAL VARS BEGIN
global mqttc
init_ok = False
nopower = False
motinprog = 0
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

IDX_READER_PWR  = 68
IDX_READER_CARD = 67
IDX_READER_PIN  = 66
PIN_READER_D0   = 6
PIN_READER_D1   = 5
PIN_READER_PWR  = 13

TEMP_COMPENSATION = 0.6
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
    cardreader.signalhandlerRemove()
    GPIO.cleanup()
    sys.exit(0)
    
def mqttPublish(msg):
    global mqttc, mqttSend
    # Publish to MQTT server
#    print(msg) # DEBUG
    mqttc.publish(mqttSend, msg)
    
def IOHandler(channel):
   global init_ok, sMot, sDor, domomsg, sUPS, lastupstime, nopower, motinprog
   if init_ok:
    msg = ""
    msg1 = ""

    if (channel == PIN_MOTION1) or (channel == PIN_MOTION2):
     lv = sMot.getlastvalue()
     nv = sMot.getpinvalue(channel)
     if (nv != lv):
       msg = domomsg.format(IDX_MOTION_C, nv, motionStates[nv])
       if (nv == 1):
        motinprog = time.time()
       else:
        motinprog = 0
     else:
      if (motinprog > 0):
       if (nv == 0):
        msg = domomsg.format(IDX_MOTION_C, nv, motionStates[nv])

    if (channel == PIN_REED):
     lv = sDor.getlastvalue()
     nv = sDor.getpinvalue(channel)
     if (nv != lv):
       msg = domomsg.format(IDX_REED, nv, motionStates[nv])

    if (channel == PIN_UPS):
     lv = sUPS.getlastvalue()
     nv = sUPS.getpinvalue(channel)
     if (nopower) and (nv == 1):
        nopower = False
     if (nv != lv) and (time.time() - lastupstime > 30):
       if (nv == 0):
        lastupstime = time.time()
        nopower = True
       msg = domomsg.format(IDX_UPS, nv, motionStates[nv])

    if msg != "":   
     mqttPublish(msg)   
    if msg1 != "":   
     mqttPublish(msg1)   

def readercallback(typecode, data):
 global cardreader

 transtext = ""
 if len(str(data))>0:
  if (typecode == 2) and (len(str(data))>1):
   if (str(data)[0] == '0'): # parancs
    transtext = str(data)
   else:
    transtext = hashlib.sha1(bytes(data,'utf-8')).hexdigest()
    if transtext[0] == '0':
     transtext[0] = '1'
#    transtext = str(data)
   msg = domomsg.format(IDX_READER_PIN, 0, transtext)
   mqttPublish(msg)
#   print(msg)
  elif (typecode == 3):
   transtext = hashlib.sha1(bytes(data,'utf-8')).hexdigest()
#   transtext = str(data)
   msg = domomsg.format(IDX_READER_CARD, 0, transtext)
   mqttPublish(msg)
#   print(msg)

def on_connect(client, userdata, flags, rc):
 global mqttc, mqttReceive
 mqttc.subscribe(mqttReceive,0)

def on_message(mosq, obj, msg):
 global oSiren
 msg2 = msg.payload.decode('utf-8')
 if ('{' in msg2):
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
   if (list['idx'] == IDX_READER_PWR): # pwr mode
     pwrmode = int(list['nvalue'])
     if (pwrmode == 0) or (pwrmode == 1):
       cardreader.setpowermode(pwrmode)
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
print("Enabling card reader")
cardreader = CardReader(PIN_READER_D0,PIN_READER_D1,readercallback,PIN_READER_PWR)
cardreader.setpowermode(1)

msg = domomsg.format(IDX_READER_PWR, 1, motionStates[1])
mqttPublish(msg)
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
motinprog = 0

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
    tvar2 = sUPS.readfinalvalue()
#    print("Battery: ",tvar2[0],"% (",tvar2[1],"V), Power IN:",tvar2[2],"V")
    if (nopower):       # only return battery status, if charging!
     batteryval = str(tvar2[0])
    else:
     batteryval = "100"
    msg = domomsgwb.format(IDX_PITMP,0,str(ctmp[0]),util.rssitodomo(ctmp[1]),batteryval)
    mqttPublish(msg)
    if (nopower) and (tvar2[0] < 10): # no mains and battery under 10 percent
     os.system("sudo /sbin/shutdown -h now")

  if sPres.isScanTime():
    preslist = sPres.doScan()
    for i in range(len(preslist)):
      msg = domomsg.format(preslist[i],1, motionStates[1])
      mqttPublish(msg)

  time.sleep(0.2)
