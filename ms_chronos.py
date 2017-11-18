# -*- coding: utf-8 -*-
DEBUGMODE = False

import sys
import os
import platform
import signal
import datetime
import time
import json
import util
import locale
import random
import re
import paho.mqtt.client as mqtt

if DEBUGMODE!=True:
 import RPi.GPIO as GPIO
 from unit_cputherm import *
 from unit_lht import *
 from unit_motion import *
 from unit_temp import *
 from unit_backlight_wpi import *
 from apds9960.const import *
 from apds9960 import APDS9960
 import smbus
 dirs = {
    APDS9960_DIR_NONE: "none",
    APDS9960_DIR_LEFT: "left",
    APDS9960_DIR_RIGHT: "right",
    APDS9960_DIR_UP: "up",
    APDS9960_DIR_DOWN: "down",
    APDS9960_DIR_NEAR: "near",
    APDS9960_DIR_FAR: "far",
 }
else:
 from clock.unit_dummy import *

from unit_sound import *

from PyQt4 import QtGui, QtCore, QtNetwork
from PyQt4.QtGui import QPixmap, QMovie, QBrush, QColor, QPainter
from PyQt4.QtCore import QUrl
from PyQt4.QtCore import Qt
from PyQt4.QtNetwork import QNetworkReply
from PyQt4.QtNetwork import QNetworkRequest
from subprocess import Popen
import clock.ApiKeys
from clock.unit_clocktimer import *

os.putenv('DISPLAY', ':0')

sys.dont_write_bytecode = True

#GLOBAL VARS BEGIN
global mqttc
mqttinit = False
#GLOBAL VARS END

motionStates  = [ "Off", "On" ]

domomsg = '{{ "idx": {0}, "nvalue": {1:0.2f}, "svalue": "{2}" }}'
domomsgsel = '{{ "idx": {0}, "nvalue": {1:0.2f}, "svalue": "{2}", "svalue1": "{2}" }}'
domomsgw = '{{ "idx": {0}, "nvalue": {1:0.2f}, "svalue": "{2}", "RSSI": {3} }}'

frontmotionstatus = [0,0]

def getTime():
    # Save a few key strokes
    return datetime.datetime.now().strftime('%H:%M:%S')

def mqttSendOrder(msg):
    global mqttc
    # Publish to MQTT server
    if DEBUGMODE!=True:
     mqttc.publish(ClockConfig.mqttReceive, msg)
    else:
     print("OUT: ",msg) # DEBUG
     
def mqttPublish(msg):
    global mqttc, mqttSend
    # Publish to MQTT server
    if DEBUGMODE!=True:
     mqttc.publish(ClockConfig.mqttSend, msg)
    else:
     print(msg) # DEBUG

def IOHandler(channel):
   global mqttinit, sMot, sMotF, domomsg, oBacklight, lastmove, frontmotionstatus
   if mqttinit:
    msg = ""
    msg1 = ""
    
    if (channel == ClockConfig.PIN_MOTION1) or (channel == ClockConfig.PIN_MOTION2):
#     print("DEBUG: ",channel)
     lv = sMot.getlastvalue()
     nv = sMot.getpinvalue(channel)
     if (nv != lv):
       msg = domomsg.format(ClockConfig.IDX_MOTION_C, nv, motionStates[nv])
       if nv == 1:
        print("Side motion")
        lastmove = time.time()
        oBacklight.set_level_light_compensated(65535)

    if (channel == ClockConfig.PIN_MOTIONFRONT):
     lv = sMotF.getlastvalue()
     nv = sMotF.getpinvalue(channel)
     frontmotionstatus[0] = nv
     if (nv != lv):
      frontmotionstatus[1] = time.time()
#     print("Front PIR det",frontmotionstatus)

    if msg != "":   
     mqttPublish(msg)   
    if msg1 != "":   
     mqttPublish(msg1)   

def on_connect(client, userdata, flags, rc):
  global mqttc, mqttReceive
  mqttc.subscribe(ClockConfig.mqttReceive,0)

def on_message(mosq, obj, msg):
  global frame3, oSiren, oRadio, theradio, MainTimer
  msg2 = msg.payload.decode('utf-8')
#  print(msg2)
  list = []
  try:
   list = json.loads(msg2)
  except Exception as e:
   print(e)
   list = []
  if (list):
#   print(list['idx'])
   if (list['idx'] == ClockConfig.IDX_SIREN):
#     print(list['svalue1']) # DEBUG
     rlevel = 0
     if list['svalue1']:
      rlevel = int(list['svalue1'])
     else:
      rlevel = int(list['svalue'])
     oSiren.play(rlevel)
     if (rlevel) == 0:
       MainTimer.alarmstopped()
     else:  
       MainTimer.alarmstarted()
   if (list['idx'] == ClockConfig.IDX_RADIO):
#     print(list['svalue1'])
     rlevel = 0
     if list['svalue1']:
      rlevel = int(list['svalue1'])
     else:
      rlevel = int(list['svalue'])
     if (rlevel) == 0:
       MainTimer.alarmstopped()
     else:  
       MainTimer.alarmstarted()
     if rlevel > 9:
      theradio.setlevel(int( (rlevel/10) -1 ) )
      theradio.play(False)
     else:
      theradio.stop(False)
     theradio.printchannel() 

def tick():
    global hourpixmap, minpixmap, secpixmap
    global hourpixmap2, minpixmap2, secpixmap2
    global lastmin, lastday, lasttimestr
    global clockrect
    global datex, datex2, datey2, pdy

    dayname = ['Hét','Ke','Sze','Csüt','Pén','Szo','Vas']

    if ClockConfig.DateLocale != "":
        try:
            locale.setlocale(locale.LC_TIME, ClockConfig.DateLocale)
        except:
            pass

    now = datetime.datetime.now()
    #print(now)
    if ClockConfig.digital:
        timestr = ClockConfig.digitalformat.format(now)
        if ClockConfig.digitalformat.find("%I") > -1:
            if timestr[0] == '0':
                timestr = timestr[1:99]
        if lasttimestr != timestr:
            clockface.setText(timestr.lower())
        lasttimestr = timestr
    else:
        angle = now.second * 6
        ts = secpixmap.size()
        secpixmap2 = secpixmap.transformed(
            QtGui.QMatrix().scale(
                float(clockrect.width()) / ts.height(),
                float(clockrect.height()) / ts.height()
            ).rotate(angle),
            Qt.SmoothTransformation
        )
        sechand.setPixmap(secpixmap2)
        ts = secpixmap2.size()
        sechand.setGeometry(
            clockrect.center().x() - ts.width() / 2,
            clockrect.center().y() - ts.height() / 2,
            ts.width(),
            ts.height()
        )
        if now.minute != lastmin:
            lastmin = now.minute
            angle = now.minute * 6
            ts = minpixmap.size()
            minpixmap2 = minpixmap.transformed(
                QtGui.QMatrix().scale(
                    float(clockrect.width()) / ts.height(),
                    float(clockrect.height()) / ts.height()
                ).rotate(angle),
                Qt.SmoothTransformation
            )
            minhand.setPixmap(minpixmap2)
            ts = minpixmap2.size()
            minhand.setGeometry(
                clockrect.center().x() - ts.width() / 2,
                clockrect.center().y() - ts.height() / 2,
                ts.width(),
                ts.height()
            )

            angle = ((now.hour % 12) + now.minute / 60.0) * 30.0
            ts = hourpixmap.size()
            hourpixmap2 = hourpixmap.transformed(
                QtGui.QMatrix().scale(
                    float(clockrect.width()) / ts.height(),
                    float(clockrect.height()) / ts.height()
                ).rotate(angle),
                Qt.SmoothTransformation
            )
            hourhand.setPixmap(hourpixmap2)
            ts = hourpixmap2.size()
            hourhand.setGeometry(
                clockrect.center().x() - ts.width() / 2,
                clockrect.center().y() - ts.height() / 2,
                ts.width(),
                ts.height()
            )

    dy = "{0:%H:%M}".format(now)
    if dy != pdy:
        pdy = dy

    if now.day != lastday:
        lastday = now.day
        ds = format(now.month,'02') + "/" + format(now.day,'02') + " " + dayname[now.weekday()]
        datex.setText(ds)

def wxfinished():
    global wxreply, wxdata
    global wxicon, temper, wxdesc#, press, humidity
    global wind, wind2, bottom, wdate, forecast, sensorarr
    global wxicon2, temper2, wxdesc

#    with open('wu.json','r') as wufile: 	# DEBUG
#     wxstr = wufile.read()
#     print(wxstr)
#     wxstr = wxstr.rstrip('\n').rstrip(' ')
    wxstr = str(wxreply.readAll(),'utf-8').rstrip('\n').rstrip(' ')
    f = []
    try:
     wxdata = json.loads( wxstr )
     f = wxdata['current_observation']
     iconurl = f['icon_url']
     icp = ''
     if (re.search('/nt_', iconurl)):
        icp = 'n_'
     wxiconpixmap = QtGui.QPixmap(ClockConfig.icons + "/" + icp + f['icon'] + ".png")
     wxicon.setPixmap(wxiconpixmap.scaled(
        wxicon.width(), wxicon.height(), Qt.IgnoreAspectRatio,
        Qt.SmoothTransformation))
    except:
     print( json.dumps(wxstr))
     f['weather'] = ''  
    wxdesc.setText(f['weather'])

    if ClockConfig.metric:
        temper.setText(str(f['temp_c']) + u'°C')
    else:
        temper.setText(str(f['temp_f']) + u'°F')
    bottom.setText(wxdata['sun_phase']['sunrise']['hour'] + ':' +
                   wxdata['sun_phase']['sunrise']['minute'] + ' ' +
                   wxdata['sun_phase']['sunset']['hour'] + ':' +
                   wxdata['sun_phase']['sunset']['minute']
                   )

    fl = sensorarr[0]
    icon = fl.findChild(QtGui.QLabel, "icon")
    wxiconpixmap = QtGui.QPixmap(ClockConfig.icons + "/temperature.png")
    icon.setPixmap(wxiconpixmap.scaled(
            icon.width(),
            icon.height(),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation))
    fl = sensorarr[1]
    icon = fl.findChild(QtGui.QLabel, "icon")
    wxiconpixmap = QtGui.QPixmap(ClockConfig.icons + "/light.png")
    icon.setPixmap(wxiconpixmap.scaled(
            icon.width(),
            icon.height(),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation))
    fl = sensorarr[2]
    icon = fl.findChild(QtGui.QLabel, "icon")
    wxiconpixmap = QtGui.QPixmap(ClockConfig.icons + "/CPU.png")
    icon.setPixmap(wxiconpixmap.scaled(
            icon.width(),
            icon.height(),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation))

    for i in range(0, 4):
       fl = forecast[i]
       try:
        f = wxdata['hourly_forecast'][i * 4 + 2]
        iconurl = f['icon_url']
        icp = ''
        if (re.search('/nt_', iconurl)):
            icp = 'n_'
        icon = fl.findChild(QtGui.QLabel, "icon")
        wxiconpixmap = QtGui.QPixmap(
            ClockConfig.icons + "/" + icp + f['icon'] + ".png")
        icon.setPixmap(wxiconpixmap.scaled(
            icon.width(),
            icon.height(),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation))
        wx = fl.findChild(QtGui.QLabel, "wx")
        wx.setText(f['condition'])
        day = fl.findChild(QtGui.QLabel, "day")
        day.setText(f['FCTTIME']['weekday_name'] + ' ' + f['FCTTIME']['hour_padded']+ ':' + f['FCTTIME']['min'])
        s = ''
        if float(f['pop']) > 0.0:
            s += f['pop'] + '% '
        if ClockConfig.metric:
            if float(f['snow']['metric']) > 0.0:
                s += ClockConfig.LSnow + f['snow']['metric'] + 'mm '
            else:
                if float(f['qpf']['metric']) > 0.0:
                    s += ClockConfig.LRain + f['qpf']['metric'] + 'mm '
            s += f['temp']['metric'] + u'°C'
        else:
            if float(f['snow']['english']) > 0.0:
                s += ClockConfig.LSnow + f['snow']['english'] + 'in '
            else:
                if float(f['qpf']['english']) > 0.0:
                    s += ClockConfig.LRain + f['qpf']['english'] + 'in '
            s += f['temp']['english'] + u'°F'
       except:
        s = ''
       wx2 = fl.findChild(QtGui.QLabel, "wx2")
       wx2.setText(s)

def getwx():
    global wxurl
    global wxreply
    print("getting current and forecast:" + time.ctime())
    wxurl = ClockConfig.wuprefix + clock.ApiKeys.wuapi + \
        '/conditions/astronomy/hourly/lang:' + \
        ClockConfig.wuLanguage + '/q/'
    wxurl += str(ClockConfig.primary_coordinates[0]) + ',' + \
        str(ClockConfig.primary_coordinates[1]) + '.json'
    wxurl += '?r=' + str(random.random())
    print(wxurl)
    r = QUrl(wxurl)
#    wxfinished() # DEBUG
    r = QNetworkRequest(r)
    wxreply = manager.get(r)
    wxreply.finished.connect(wxfinished)


def getallwx():
    getwx()

def sensors():
  global sLight, sTemp, sCPU, oSiren, oRadio, oBacklight, MainTimer
  global sensorarr, lastmove, framep, screenstarttime, frontmotionstatus

  if sTemp.isValueFinal():
    atmp, ahum, ahs = sTemp.readfinalvalue()
    msg = domomsg.format(ClockConfig.IDX_TMP, 0, (str(atmp) + ";" + str(ahum) + ";" + str(ahs)) )
    mqttPublish(msg)
    fl = sensorarr[0]
    wx = fl.findChild(QtGui.QLabel, "wx2")
    wx.setText(str(atmp)+ u'°C ' + str(ahum) + '%')
  else:
    sTemp.readvalue()

  if sLight.isValueFinal():
    alht = sLight.readfinalvalue()
    msg = domomsg.format(ClockConfig.IDX_LHT, 0, str(alht) )
    mqttPublish(msg)
    fl = sensorarr[1]
    wx = fl.findChild(QtGui.QLabel, "wx2")
    wx.setText(str(alht) + 'lx')
    nomovetime = (time.time() - lastmove)
    if (nomovetime > 30):
     oBacklight.set_level(oBacklight.get_level()-5)
     if (nomovetime > ClockConfig.DisplayOffTime):
      if (oBacklight.get_level() >0):
       oBacklight.set_off()
#       print("Backlight off "+str(nomovetime))
    else:
      oBacklight.set_level_light_compensated(alht)
  else:
    sLight.readvalue()

  if sCPU.isValueFinal():
    ctmp = sCPU.readfinalvalue()
    msg = domomsgw.format(ClockConfig.IDX_PITMP,0, str(ctmp[0]),util.rssitodomo(ctmp[1]))
    mqttPublish(msg)
    fl = sensorarr[2]
    wx = fl.findChild(QtGui.QLabel, "wx2")
    wx.setText(str(ctmp[0])+ u'°C')
    
  MainTimer.TimerPeriodicCheck()
  if framep != 0:
   if (time.time() - screenstarttime) > ClockConfig.ReturnHomeSec: # return to home screen
     nextframe( (framep * (-1)) )

  if frontmotionstatus[0] == 1:
#   print("FM2",frontmotionstatus)
   if (time.time() - frontmotionstatus[1])>ClockConfig.FrontMotionMinMove:
#    print("Front motion")
    oBacklight.set_level_light_compensated(65535)
    lastmove = time.time()
    frontmotionstatus[0] = 0

def qtstart():
    global ctimer, stimer, wxtimer
    global sMot, sLight, sTemp, sCPU, oSiren, oRadio, oBacklight, sMotF
    global manager, mqttc, lastmove
    global mqttinit, apds

    getallwx()
    mqttc = mqtt.Client("", True, None, mqtt.MQTTv31)
    
    # PROGRAM INIT
    if DEBUGMODE!=True:
     GPIO.setwarnings(False)
     GPIO.setmode(GPIO.BCM)
    print("MQTT connection")
    mqttinit = True
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    try:
     mqttc.connect(ClockConfig.mqttServer, 1883)
    except:
     mqttinit = False
     print('MQTT server not found')
     sys.exit(0)

    lastmove = time.time()
    print("Setup motion sensor")
    sMot   = Motion(IOHandler,ClockConfig.PIN_MOTION1,ClockConfig.PIN_MOTION2)
    print("Setup front motion sensor")
    sMotF  = Motion(IOHandler,ClockConfig.PIN_MOTIONFRONT)
    print("Setup light sensor")
    sLight = BH1750(ClockConfig.tempdelaysec)
    print("Setup temperature sensor")
    sTemp  = DHT(ClockConfig.PIN_TMP,ClockConfig.tempdelaysec)
    print("Setup CPU thermal sensor")
    sCPU   = CPUThermal(0,ClockConfig.tempdelaysec,True)
    print("Setup sound outputs")
    oSiren = Siren()
    oRadio = Radio()
    print("Setup backlight control")
    oBacklight = BacklightControl(ClockConfig.PIN_TFT_LED)
    if DEBUGMODE!=True:
     print("Setup APDS9960")
     GPIO.setup(ClockConfig.PIN_ADPS, GPIO.IN) # ADPS INT
     try:
      bus = smbus.SMBus(1)
      apds = APDS9960(bus)
      apds.setProximityIntLowThreshold(50)
      apds.enableGestureSensor()
     except:
      print("APDS init error")
     GPIO.add_event_detect(ClockConfig.PIN_ADPS, GPIO.FALLING, callback = gesturehandler)

    if mqttinit:
     msg = domomsg.format(ClockConfig.IDX_MOTION_C, sMot.getlastvalue(), motionStates[sMot.getlastvalue()])
     mqttPublish(msg)
     mqttc.loop_start()

    ctimer = QtCore.QTimer()
    ctimer.timeout.connect(tick)
    ctimer.start(1000)

    stimer = QtCore.QTimer()
    stimer.timeout.connect(sensors)
    stimer.start(2000)

    wxtimer = QtCore.QTimer()
    wxtimer.timeout.connect(getallwx)
    wxtimer.start(1000 * ClockConfig.weather_refresh *
                  60 + random.uniform(1000, 10000))

class Radiohandler():
 global oRadio, frame3

 def __init__(self):
   self.playing = False
   self.activelevel = 0
   self.printchannel()

 def printchannel(self):
  tstr = config_sound.radiostations[self.activelevel][0]
  guitxt = frame3.findChild(QtGui.QLabel, "radiotxt")
  guitxt.setText(tstr)
  
 def setlevel(self,level):
  if (level >= 0) and (level < len(config_sound.radiostations)):
   self.activelevel = level

 def isplaying(self):
  return self.playing

 def levelup(self):
  if (self.activelevel < len(config_sound.radiostations)-1):
   self.activelevel += 1
  else:
   self.activelevel = 0
  if (self.playing):
   self.play()
  self.printchannel()

 def leveldown(self):
  if (self.activelevel > 0):
   self.activelevel -= 1
  else:
   self.activelevel = len(config_sound.radiostations)-1
  if (self.playing):
   self.play()
  self.printchannel()

 def play(self,DoReply=True):
   self.playing = True
   oRadio.play((self.activelevel+1)*10)
   if DoReply:
    msg = domomsgsel.format(ClockConfig.IDX_RADIO, 2, str( (self.activelevel+1)*10 ))
    mqttPublish(msg)
    print(msg)
   guitxt2 = frame3.findChild(QtGui.QLabel, "radiotxt2")
   guitxt2.setText("Lejátszás")

 def stop(self,DoReply=True):
   self.playing = False
   oRadio.stop()
   if DoReply:
    msg = domomsgsel.format(ClockConfig.IDX_RADIO, 0, '0')
    mqttPublish(msg)
   guitxt2 = frame3.findChild(QtGui.QLabel, "radiotxt2")
   guitxt2.setText("Megállítva")

 def startstop(self):
   if (self.playing):
    self.stop()
   else:
    self.play()

def realquit():
    QtGui.QApplication.exit(0)


def myquit(a=0, b=0):
    global ctimer, wxtimer, stimer
    global mqttc, mqttinit
    global sMot, oBacklight, sMotF
    # Clean up on CTRL-C
    #print('\r\n' + getTime() + ': Exiting...')
    oBacklight.set_on()
    if mqttinit:
     try:
      mqttc.loop_stop()
      mqttc.disconnect()
     except:
      pass
    sMot.signalhandlerRemove()
    sMotF.signalhandlerRemove()
    ctimer.stop()
    wxtimer.stop()
    stimer.stop()
    if DEBUGMODE!=True:
     GPIO.cleanup()

    QtCore.QTimer.singleShot(30, realquit)
    sys.exit(0)

def nextframe(plusminus):
    global frames, framep, screenstarttime
    frames[framep].setVisible(False)
#    fixupframe(frames[framep], False)
    framep += plusminus
    if framep >= len(frames):
        framep = 0
    if framep < 0:
        framep = len(frames) - 1
    frames[framep].setVisible(True)
#    fixupframe(frames[framep], True)
    screenstarttime = time.time()

def gesturehandler(channel): # kezmozdulatok alapjan vezerel
 global apds, w, framep, lastmove
 detect = False
 if apds.isGestureAvailable():
      motion = apds.readGesture()
      if (motion == APDS9960_DIR_LEFT):
        w.insignal.emit(-1) # balra lapoz
        detect = True
      if (motion == APDS9960_DIR_RIGHT):
        w.insignal.emit(1) # jobbra lapoz
        detect = True

      if (framep == 0):
       if (motion == APDS9960_DIR_UP):
        w.insignal.emit(11) # vilagitas fel
        detect = True
       if (motion == APDS9960_DIR_DOWN):
        w.insignal.emit(12) # vilagitas le
        detect = True
       if (motion == APDS9960_DIR_NEAR) or (motion == APDS9960_DIR_FAR):
        w.insignal.emit(13) # hang/riasztas lekapcs
        detect = True
       if detect == False:
        w.insignal.emit(13) # vegso esetben riasztas lekapcs

      if (framep == 2):
       if (motion == APDS9960_DIR_UP):
        w.insignal.emit(21) # elozo csatorna
        detect = True
       if (motion == APDS9960_DIR_DOWN):
        w.insignal.emit(22) # kovetkezo csatorna
        detect = True
       if (motion == APDS9960_DIR_NEAR) or (motion == APDS9960_DIR_FAR):
        w.insignal.emit(23) # lejatszas/megallitas
        detect = True

#      print("ADPS move")
      lastmove = time.time()
      oBacklight.set_level_light_compensated(65535)

def buttonhandler(name): # gombra kattintasokat kezeli minden kepernyon
    global MainTimer, theradio, w
#    print('"%s" clicked' % name)
    if (name == "play"):
     w.insignal.emit(10)      
     theradio.startstop()
    if (name == "up"):
     w.insignal.emit(10)      
     theradio.levelup()
    if (name == "down"):
     w.insignal.emit(10)     
     theradio.leveldown()
    if (name == "mticon"):
     w.insignal.emit(10)
     w.insignal.emit(13) # hang/riasztas lekapcs      
    if (name == "alicon"):
     w.insignal.emit(10)
     alist = AlarmList(MainTimer)
     w.setWindowState(QtCore.Qt.WindowNoState)
     showmaximizedwindow(alist)

class ClickableLabel(QtGui.QLabel):
    clicked = QtCore.pyqtSignal(str)

    def mousePressEvent(self, event):
        self.clicked.emit(self.objectName())

class myMain(QtGui.QWidget):
    global framep
    insignal = QtCore.pyqtSignal(int)
    mousex = 0
    mousey = 0

    def __init__(self):
     QtGui.QWidget.__init__(self)
     self.insignal.connect(self.intercom)

    def intercom(self, msg): # mas szalrol erkezett parancsok ertelmezese es tovabbitasa
     if (msg == 1):
      nextframe(1)
     if (msg == -1):
      nextframe(-1)
     if (msg == 10): # correct icon clicks
      if DEBUGMODE!=True:       
       apos = QtGui.QCursor.pos() 
       self.mousex = apos.x()
       self.mousey = apos.y()       
      else:
       pass
     if (msg == 11) or (msg == 12) or (msg == 13):
      self.MQTTCommander(msg)
     if (msg == 21):
      buttonhandler("up")
     if (msg == 22):
      buttonhandler("down")
     if (msg == 23):
      buttonhandler("play")

#     print(msg)

# Function to detect swipes mouse/touchscreen
# -1 is that it was not detected as a swipe or click
# It will return 1:right , 2:left for horizontal swipe
# If the swipe is vertical will return 3:down, 4:up
# If it was a click it will return 0
    def getSwipeType(self,x,y):
       minSwipe = 50
       maxClick = 15
       if abs(x)<=minSwipe:
        if abs(y)<=minSwipe:
            if abs(x) < maxClick and abs(y)< maxClick:
                return 0
            else:
                return -1
        elif y>minSwipe:
            return 3
        elif y<-minSwipe:
            return 4
       elif abs(y)<=minSwipe:
        if x>minSwipe:
           return 1
        elif x<-minSwipe:
           return 2
       return 0

    def keyPressEvent(self, event):
        global weatherplayer, lastkeytime
        if isinstance(event, QtGui.QKeyEvent):
            # print event.key(), format(event.key(), '08x')
            if event.key() == Qt.Key_F4:
                myquit()
            if event.key() == Qt.Key_Space:
                nextframe(1)
            if event.key() == Qt.Key_Left:
                nextframe(-1)
            if event.key() == Qt.Key_Right:
                nextframe(1)

    def mousePressEvent(self, event):
        self.mousex = event.x()
        self.mousey = event.y()
#            nextframe(1)

    def mouseReleaseEvent(self, event):
        global w
        if type(event) == QtGui.QMouseEvent:
            swipe = self.getSwipeType(event.x()-self.mousex,event.y()-self.mousey)
            self.mousex = event.x()
            self.mousey = event.y()
            if (swipe > 0):
             if (swipe == 1):
              nextframe(1)
             if (swipe == 2):
              nextframe(-1)
             if (framep == 2):
              if (swipe == 4):
               buttonhandler("up")
              if (swipe == 3):
               buttonhandler("down")
             if (framep == 0):
              if (swipe == 4):
               w.insignal.emit(11) # vilagitas fel               
              if (swipe == 3):
               w.insignal.emit(12) # vilagitas le
#            print(swipe)

    def MQTTCommander(self, code):         
      global MainTimer, oBacklight
      if code==11: # lampa bekapcs
       msg = domomsg.format(ClockConfig.Light_MQTT_IDX, 1, motionStates[1])
       mqttPublish(msg)
       oBacklight.set_level(100)
#       mqttSendOrder(msg)
#       print("MQTT",msg)
      elif code==12: # riasztas le, vagy lampa le
       if MainTimer.isalarmactive():        
        alarmhandler(0)        
        MainTimer.alarmstopped()
       else: # lampa lekapcs
        msg = domomsg.format(ClockConfig.Light_MQTT_IDX, 0, motionStates[0])
#        mqttSendOrder(msg)
        mqttPublish(msg)
#        print("MQTT",msg)
      elif code==13:
       print("Mute")
       if MainTimer.isalarmactive():
        alarmhandler(0)
        MainTimer.alarmstopped()

def showmaximizedwindow(awindow):
 global DEBUGMODE
 if DEBUGMODE!=True:
  desktop = QtGui.QApplication.desktop()
  sg = desktop.availableGeometry()
  awindow.resize(sg.width(),sg.height())
  awindow.move(0,0)
  awindow.showMaximized()
 else:
  awindow.resize(320,240)
 awindow.exec_()

class AlarmList(QtGui.QDialog):
    def __init__(self, DataProv, parent=None):
        global height
        super(AlarmList, self).__init__(parent)
        mainLayout = QtGui.QGridLayout()
        
        self.DataProvider = DataProv
        if (height < 240):
         height = 240
        self.font = QtGui.QFont()
        self.font.setPointSize(int(height/20))
        self.setWindowTitle("Ébresztések listája")
#        self.resize(320, 240)   
        self.lista = QtGui.QListWidget()
        self.lista.setFont(self.font)

        horizontalLayout = QtGui.QHBoxLayout()
        pushButtonB1 = QtGui.QPushButton()
        pushButtonB1.setText("Új");
        pushButtonB1.clicked.connect(self.addListelement)        
        pushButtonB2 = QtGui.QPushButton()
        pushButtonB2.setText("Módosít");
        pushButtonB2.clicked.connect(self.modifyListelement)        
        pushButtonB3 = QtGui.QPushButton()
        pushButtonB3.setText("Törlés")
        pushButtonB3.clicked.connect(self.delListelement)
        pushButtonB4 = QtGui.QPushButton()        
        pushButtonB4.setText("Kilépés")
#        pushButtonB4.clicked.connect(QtCore.QCoreApplication.instance().quit)
        pushButtonB4.clicked.connect(self.niceclose)        

        horizontalLayout.addWidget(pushButtonB1)
        horizontalLayout.addWidget(pushButtonB2)
        horizontalLayout.addWidget(pushButtonB3)
        horizontalLayout.addWidget(pushButtonB4)        

        label1 = QtGui.QLabel("Ébresztések:")
        mainLayout.addWidget(label1,0,0,1,1)
        mainLayout.addWidget(self.lista,1,0,1,1)
        #(self, QWidget, int row, int column, int rowSpan, int columnSpan, Qt.Alignment alignment = 0)
        mainLayout.addLayout(horizontalLayout, 2,0,1,1)
        #(self, QLayout, int row, int column, int rowSpan, int columnSpan, Qt.Alignment alignment = 0)
        self.setLayout(mainLayout)
        self.refreshlist()

    def niceclose(self):
     global w, DEBUGMODE
     self.close()
     w.show()
     if DEBUGMODE!=True:
      w.showFullScreen()

    def refreshlist(self):
      self.lista.clear()
      slist = self.DataProvider.getscenelist()
#      for i in range(len(slist)): 
#        print(slist[i])    # DEBUG
      alist = self.DataProvider.getalarmlist()
      try:
       for i in range(len(alist)): 
#        print(alist[i])     # DEBUG
        datas = ""
        if (int(alist[i][2]) == 1):  # enabled
         if (int(alist[i][3]) == TIMER_T_ONTIME):
          if (int(alist[i][7]) == DAY_EVERY):
           datas = "Mindennap"
          elif (int(alist[i][7]) == DAY_WEEKDAY):
           datas = "Hétköznap"           
          elif (int(alist[i][7]) == DAY_WEEKEND):
           datas = "Hétvége"           
          else:
           datas = "Adott napokon: " 
           if (int(alist[i][7]) & DAY_MON):
            datas = datas + "Hé "
           if (int(alist[i][7]) & DAY_TUE):
            datas = datas + "Ke "
           if (int(alist[i][7]) & DAY_WED):
            datas = datas + "Sze "
           if (int(alist[i][7]) & DAY_THU):
            datas = datas + "Csü "
           if (int(alist[i][7]) & DAY_FRI):
            datas = datas + "Pé "
           if (int(alist[i][7]) & DAY_SAT):
            datas = datas + "Szo "
           if (int(alist[i][7]) & DAY_SUN):
            datas = datas + "Va "
         elif (int(alist[i][3]) == TIMER_T_FIXED_DATE):
          datas = "Adott dátum: "+alist[i][4]
         datas += " " + str(alist[i][5]) + ":" + str(alist[i][6])
      #sceneidx, timeridx, enabled, type, date, hour, minute, days, next epochtime
         #print(datas)
         datas += " Profil: "
         for j in range(len(slist)):
          if (slist[j][0] == alist[i][0]):
           datas += slist[j][1]
         item = QtGui.QListWidgetItem(datas)
         self.lista.addItem(item)
      except:
       pass
     
    def addListelement(self, MIDX=0):
      self.close()
      self.ap = AlarmParams(self.DataProvider,MIDX)
      showmaximizedwindow(self.ap)

    def modifyListelement(self):
      tidx = (self.lista.currentRow()+1)
      self.addListelement(tidx)
        
    def delListelement(self):
      alist = self.DataProvider.getalarmlist()
      try:
       tidx = alist[self.lista.currentRow()][1]
      except:
       pass     
      self.DataProvider.delalarm(tidx)        # DEBUG
      for item in self.lista.selectedItems():
        self.lista.takeItem(self.lista.row(item))
#      result = QtGui.QMessageBox.about(self, 'Delete timer', str(tidx)) # debug

class AlarmParams(QtGui.QDialog):
    def __init__(self, DataProv, ModIDX=0, parent=None):
        global height
        super(AlarmParams, self).__init__(parent)
        mainLayout2 = QtGui.QGridLayout()
        
        if height < 240:
         height = 240
        self.font = QtGui.QFont()
        self.font.setPointSize(int(height/12))
        self.DataProvider = DataProv        
        self.setWindowTitle("Ébresztés paraméterei")
#        self.resize(320, 240)   

        slist = self.DataProvider.getscenelist()         
        #print(slist)
        selmode = None
        selprof = None
        dayinfo = 0
        self.modidx = 0
        dtvar = datetime.datetime.now()
        seldate = QtCore.QDate(int(dtvar.strftime("%Y")),int(dtvar.strftime("%m")),int(dtvar.strftime("%d")))
        seltime = QtCore.QTime(int(dtvar.strftime("%H")),int(dtvar.strftime("%M")),0)
        if int(ModIDX) > 0:
         alist = self.DataProvider.getalarmlist()          
         i = (ModIDX-1)
         try:
          self.modidx = alist[i][1] 
          if int(alist[i][2]) == 1: # if enabled
           dayinfo = int(alist[i][7])
           for j in range(len(slist)):
            if (slist[j][0] == alist[i][0]):
             selprof = slist[j][1]
           seltime = QtCore.QTime(int(alist[i][5]),int(alist[i][6]),0)
           if (int(alist[i][3]) == TIMER_T_ONTIME):
            if (int(alist[i][7]) == DAY_EVERY):
             selmode = "Mindennap"
            elif (int(alist[i][7]) == DAY_WEEKDAY):
             selmode = "Hétköznap"
            elif (int(alist[i][7]) == DAY_WEEKEND):
             selmode = "Hétvége"
            else:
             selmode = "Adott napokon"
           elif (int(alist[i][3]) == TIMER_T_FIXED_DATE):
            selmode = "Adott dátum"
            dtarr = alist[i][4].split("-")
            seldate = QtCore.QDate(int(dtarr[2]),int(dtarr[0]),int(dtarr[1]))
         except:
          pass

        self.napok = QtGui.QGroupBox()
        napoklayout = QtGui.QVBoxLayout()
        self.nap1 = QtGui.QCheckBox("Hétfő",self.napok)
        self.nap2 = QtGui.QCheckBox("Kedd",self.napok)
        self.nap3 = QtGui.QCheckBox("Szerda",self.napok)
        self.nap4 = QtGui.QCheckBox("Csütörtök",self.napok)
        self.nap5 = QtGui.QCheckBox("Péntek",self.napok)
        self.nap6 = QtGui.QCheckBox("Szombat",self.napok)
        self.nap7 = QtGui.QCheckBox("Vasárnap",self.napok)                
        napoklayout.addWidget(self.napok)
        napoklayout.addWidget(self.nap1)
        napoklayout.addWidget(self.nap2)        
        napoklayout.addWidget(self.nap3)        
        napoklayout.addWidget(self.nap4)        
        napoklayout.addWidget(self.nap5)        
        napoklayout.addWidget(self.nap6)        
        napoklayout.addWidget(self.nap7)        
#        napok.setLayout(napoklayout)
        if (dayinfo & DAY_MON):
         self.nap1.setChecked(True)
        if (dayinfo & DAY_TUE):         
         self.nap2.setChecked(True)      
        if (dayinfo & DAY_WED):
         self.nap3.setChecked(True)      
        if (dayinfo & DAY_THU):
         self.nap4.setChecked(True)      
        if (dayinfo & DAY_FRI):
         self.nap5.setChecked(True)      
        if (dayinfo & DAY_SAT):
         self.nap6.setChecked(True)      
        if (dayinfo & DAY_SUN):
         self.nap7.setChecked(True)                    

        verticalLayout = QtGui.QVBoxLayout()
        label1 = QtGui.QLabel("Ébresztési idő:")
        self.atime  = QtGui.QTimeEdit()
        self.atime.setFont(self.font)
        self.atime.setObjectName("atime")
        self.atime.setStyleSheet("#atime::up-button {width: 30px;} #atime::down-button {width: 30px;}")
        if seltime != None and seltime != False:
         self.atime.setTime(seltime)
        label3 = QtGui.QLabel("Profil:")
        self.profile = QtGui.QComboBox()
        self.profile.clear()
        parr = []
        try:
         for i in range(len(slist)):
          parr.append(slist[i][1])
        except:
         pass
        self.profile.addItems(parr)  
        if self.modidx != 0:
         self.profile.setEnabled(False)
#        print(selprof)
        if selprof != None and selprof != False:
         index = self.profile.findText(selprof, QtCore.Qt.MatchFixedString)
         if index >= 0:
          self.profile.setCurrentIndex(index)         

        self.adate  = QtGui.QDateEdit()
        self.adate.setCalendarPopup(True)       
        if seldate != None and seldate != False:
         self.adate.setDate(seldate)

        label2 = QtGui.QLabel("Ütemezés:")       
        self.amode = QtGui.QComboBox()
        self.amode.clear()
        self.amode.addItems(["Mindennap","Hétköznap","Hétvége","Adott dátum","Adott napokon"])
 #       print(selmode)
        self.amode.currentIndexChanged['QString'].connect(self.AlertModeChanged)

        if selmode != None and selmode != False:
         index = self.amode.findText(selmode, QtCore.Qt.MatchFixedString)
#         print(index)
         if index >= 0:
          self.amode.setCurrentIndex(index)
        else:
          selmode = "Mindennap" 
        self.AlertModeChanged(selmode)
       
        verticalLayout.addWidget(label1)
        verticalLayout.addWidget(self.atime)        
        verticalLayout.addWidget(label3)
        verticalLayout.addWidget(self.profile)        
        verticalLayout.addWidget(label2)        
        verticalLayout.addWidget(self.amode)
        verticalLayout.addWidget(self.adate)
               
#        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
#        buttonBox.accepted.connect(self.saveandexit)
#        buttonBox.rejected.connect(self.donotsave)

        pushButtonB1 = QtGui.QPushButton()
        pushButtonB1.setText("Mentés");
        pushButtonB1.clicked.connect(self.saveandexit)        
        pushButtonB2 = QtGui.QPushButton()
        pushButtonB2.setText("Kilépés");
        pushButtonB2.clicked.connect(self.donotsave)        

        #(self, QLayout, int row, int column, int rowSpan, int columnSpan, Qt.Alignment alignment = 0)
        mainLayout2.addLayout(verticalLayout, 0,0,1,1)
        mainLayout2.addLayout(napoklayout, 0,1,1,1)
        #(self, QWidget, int row, int column, int rowSpan, int columnSpan, Qt.Alignment alignment = 0)      
#        mainLayout2.addWidget(buttonBox,1,0,1,2)
        mainLayout2.addWidget(pushButtonB1,1,0,1,1)
        mainLayout2.addWidget(pushButtonB2,1,1,1,1)
        
        self.setLayout(mainLayout2)
        
    def AlertModeChanged(self,str1=""):
#      print("valtozas",str1)
      self.adate.setEnabled(False)
      if self.nap1.isEnabled:
       self.nap1.setEnabled(False)
       self.nap2.setEnabled(False)      
       self.nap3.setEnabled(False)      
       self.nap4.setEnabled(False)      
       self.nap5.setEnabled(False)      
       self.nap6.setEnabled(False)      
       self.nap7.setEnabled(False)            
      if (str1 != ""):
       if (str1 == "Adott dátum"):
        self.adate.setEnabled(True)
        self.nap1.setChecked(False)
        self.nap2.setChecked(False)      
        self.nap3.setChecked(False)      
        self.nap4.setChecked(False)      
        self.nap5.setChecked(False)      
        self.nap6.setChecked(False)      
        self.nap7.setChecked(False)                    
       elif (str1 == "Adott napokon"):
        if self.nap1.isEnabled() == False: 
         self.nap1.setEnabled(True)
         self.nap2.setEnabled(True)        
         self.nap3.setEnabled(True)
         self.nap4.setEnabled(True)
         self.nap5.setEnabled(True)
         self.nap6.setEnabled(True)
         self.nap7.setEnabled(True)
       elif (str1 == "Mindennap"):
        self.nap1.setChecked(True)
        self.nap2.setChecked(True)      
        self.nap3.setChecked(True)      
        self.nap4.setChecked(True)      
        self.nap5.setChecked(True)      
        self.nap6.setChecked(True)      
        self.nap7.setChecked(True)                    
       elif (str1 == "Hétköznap"):
        self.nap1.setChecked(True)
        self.nap2.setChecked(True)      
        self.nap3.setChecked(True)      
        self.nap4.setChecked(True)      
        self.nap5.setChecked(True)      
        self.nap6.setChecked(False)      
        self.nap7.setChecked(False)                    
       elif (str1 == "Hétvége"):
        self.nap1.setChecked(False)
        self.nap2.setChecked(False)      
        self.nap3.setChecked(False)      
        self.nap4.setChecked(False)      
        self.nap5.setChecked(False)      
        self.nap6.setChecked(True)      
        self.nap7.setChecked(True)                    
         
#      ["Mindennap","Hétköznap","Hétvége","Adott dátum","Adott napokon"])     
    def saveandexit(self):       
      pdate = ""
      pttype = TIMER_T_ONTIME
      pdays  = 0     
      #["Mindennap","Hétköznap","Hétvége","Adott dátum","Adott napokon"]
      modestr = self.amode.currentText()
      if modestr == "Mindennap":
       pdays = DAY_EVERY
      elif modestr == "Hétköznap":
       pdays = DAY_WEEKDAY
      elif modestr == "Hétvége":
       pdays = DAY_WEEKEND       
      elif modestr == "Adott dátum":
       pttype = TIMER_T_FIXED_DATE      
       pdate = format(self.adate.date().month(),'02') + "-" + format(self.adate.date().day(),'02') + "-"+ str(self.adate.date().year())
      else: # het napjainak elemzese 
       if self.nap1.isChecked():
        pdays += DAY_MON
       if self.nap2.isChecked():
        pdays += DAY_TUE
       if self.nap3.isChecked():
        pdays += DAY_WED
       if self.nap4.isChecked():
        pdays += DAY_THU
       if self.nap5.isChecked():
        pdays += DAY_FRI
       if self.nap6.isChecked():
        pdays += DAY_SAT
       if self.nap7.isChecked():
        pdays += DAY_SUN
      phour = format(self.atime.time().hour(),'02')
      pmin = format(self.atime.time().minute(),'02')
#      print(pdate, phour,":",pmin,pttype,pdays)
      if int(self.modidx) > 0: # update
       #timeridx, pdate, phour, pmin, pttype, pdays
       self.DataProvider.updatealarm(self.modidx,pdate,phour,pmin,pttype,pdays)
      else: # insert
       profilnev = self.profile.currentText()
       slist = self.DataProvider.getscenelist()         
       sceneidx = 0
       for j in range(len(slist)):
        if (slist[j][1] == profilnev):
         sceneidx = slist[j][0]
       if sceneidx != 0:
        self.DataProvider.addalarm(sceneidx,pdate,phour,pmin,pttype,pdays)
        #sceneidx, pdate, phour, pmin, pttype, pdays       
      self.donotsave()
      #self.alist.refreshlist()
      
    def donotsave(self):
      self.close()
      self.alist = AlarmList(self.DataProvider)
      showmaximizedwindow(self.alist)

def alarmhandler(state):
  global oSiren, theradio
  if (state == 0):
   print('alarm off')
   oSiren.stop()
   msg = domomsgsel.format(ClockConfig.IDX_SIREN, 0, '0')
   mqttPublish(msg)
   if theradio.isplaying():
    theradio.stop(True)
  else:
   print('alarm force on')
   oSiren.play(10)
   msg = domomsg.format(ClockConfig.IDX_RADIO, 2, str( 10 ))
   mqttPublish(msg)


configname = 'ClockConfig'

if len(sys.argv) > 1:
    configname = sys.argv[1]

if not os.path.isfile(configname + ".py"):
    print( "Config file not found %s" % configname + ".py")
    exit(1)

ClockConfig = __import__(configname)

# define default values for new/optional config variables.

try:
    ClockConfig.metric
except AttributeError:
    ClockConfig.metric = 1

try:
    ClockConfig.weather_refresh
except AttributeError:
    ClockConfig.weather_refresh = 30   # minutes

try:
    ClockConfig.fontattr
except AttributeError:
    ClockConfig.fontattr = ''

try:
    ClockConfig.DateLocale
except AttributeError:
    ClockConfig.DateLocale = ''

try:
    ClockConfig.digital
except AttributeError:
    ClockConfig.digital = 0

try:
    ClockConfig.wuLanguage
except AttributeError:
    ClockConfig.wuLanguage = "EN"


lastmin = -1
lastday = -1
pdy = ""
lasttimestr = ""
weatherplayer = None
lastkeytime = 0
lastapiget = time.time()

app = QtGui.QApplication(sys.argv)
desktop = app.desktop()
rec = desktop.screenGeometry()
height = rec.height()
width = rec.width()
if DEBUGMODE==True:
 height = 240
 width = 320

signal.signal(signal.SIGINT, myquit)

w = myMain()
w.setWindowTitle(os.path.basename(__file__))

w.setStyleSheet("QWidget { background-color: black;}")

# fullbgpixmap = QtGui.QPixmap(Config.background)
# fullbgrect = fullbgpixmap.rect()
# xscale = float(width)/fullbgpixmap.width()
# yscale = float(height)/fullbgpixmap.height()

xscale = float(width) / 1440.0
yscale = float(height) / 900.0

frames = []
framep = 0

frame1 = QtGui.QFrame(w)
frame1.setObjectName("frame1")
frame1.setGeometry(0, 0, width, height)
frame1.setStyleSheet("#frame1 { background-color: black; border-image: url(" +
                     ClockConfig.background + ") 0 0 0 0 stretch stretch;}")
frames.append(frame1)

frame2 = QtGui.QFrame(w)
frame2.setObjectName("frame2")
frame2.setGeometry(0, 0, width, height)
frame2.setStyleSheet("#frame2 { background-color: blue; border-image: url(" +
                     ClockConfig.background + ") 0 0 0 0 stretch stretch;}")
frame2.setVisible(False)
frames.append(frame2)

frame3 = QtGui.QFrame(w)
frame3.setObjectName("frame3")
frame3.setGeometry(0, 0, width, height)
frame3.setStyleSheet("#frame3 { background-color: blue; border-image: url(" +
                     ClockConfig.background + ") 0 0 0 0 stretch stretch;}")
frame3.setVisible(False)
frames.append(frame3)

squares1 = QtGui.QFrame(frame1)
squares1.setObjectName("squares1")
squares1.setGeometry(0, height - yscale * 600, xscale * 340, yscale * 600)
squares1.setStyleSheet(
    "#squares1 { background-color: transparent; border-image: url(" +
    ClockConfig.squares1 +
    ") 0 0 0 0 stretch stretch;}")
if not ClockConfig.digital:
    clockface = QtGui.QFrame(frame1)
    clockface.setObjectName("clockface")
#    clockrect = QtCore.QRect(
#        width / 2 - height * .4,
#        height * .45 - height * .4,
#        height * .8,
#        height * .8)
    clockrect = QtCore.QRect(
        (width-height),
        0,
        height,
        height)
    clockface.setGeometry(clockrect)
    clockface.setStyleSheet(
        "#clockface { background-color: transparent; border-image: url(" +
        ClockConfig.clockface +
        ") 0 0 0 0 stretch stretch;}")

    hourhand = QtGui.QLabel(frame1)
    hourhand.setObjectName("hourhand")
    hourhand.setStyleSheet("#hourhand { background-color: transparent; }")

    minhand = QtGui.QLabel(frame1)
    minhand.setObjectName("minhand")
    minhand.setStyleSheet("#minhand { background-color: transparent; }")

    sechand = QtGui.QLabel(frame1)
    sechand.setObjectName("sechand")
    sechand.setStyleSheet("#sechand { background-color: transparent; }")

    hourpixmap = QtGui.QPixmap(ClockConfig.hourhand)
    hourpixmap2 = QtGui.QPixmap(ClockConfig.hourhand)
    minpixmap = QtGui.QPixmap(ClockConfig.minhand)
    minpixmap2 = QtGui.QPixmap(ClockConfig.minhand)
    secpixmap = QtGui.QPixmap(ClockConfig.sechand)
    secpixmap2 = QtGui.QPixmap(ClockConfig.sechand)
else:
    clockface = QtGui.QLabel(frame1)
    clockface.setObjectName("clockface")
    clockrect = QtCore.QRect(
        (width-height),
        0,
        height,
        height)
    clockface.setGeometry(clockrect)
    dcolor = QColor(ClockConfig.digitalcolor).darker(0).name()
    lcolor = QColor(ClockConfig.digitalcolor).lighter(120).name()
    clockface.setStyleSheet(
        "#clockface { background-color: transparent; font-family:sans-serif;" +
        " font-weight: light; color: " +
        lcolor +
        "; background-color: transparent; font-size: " +
        str(int(ClockConfig.digitalsize * xscale)) +
        "px; " +
        ClockConfig.fontattr +
        "}")
    clockface.setAlignment(Qt.AlignCenter)
    clockface.setGeometry(clockrect)
#    glow = QtGui.QGraphicsDropShadowEffect()
#    glow.setOffset(0)
#    glow.setBlurRadius(50)
#    glow.setColor(QColor(dcolor))
#    clockface.setGraphicsEffect(glow)

alicon = ClickableLabel(frame1)
#alicon = QtGui.QLabel(frame1)
alicon.setObjectName("alicon")
alicon.setStyleSheet("#alicon { background-color: transparent; }")
aliconpixmap = QtGui.QPixmap(ClockConfig.icons + "/alarm-clock.png")
gw = alicon.height()*1.5
alicon.setPixmap(aliconpixmap.scaled(
 gw, gw, Qt.IgnoreAspectRatio,
 Qt.SmoothTransformation))
alicon.setGeometry(width-gw, 0, gw, gw)
alicon.clicked.connect(buttonhandler)

#mticon = QtGui.QLabel(frame1)
mticon = ClickableLabel(frame1)
mticon.setObjectName("mticon")
mticon.setStyleSheet("#mticon { background-color: transparent; }")
mticonpixmap = QtGui.QPixmap(ClockConfig.icons + "/mute.png")
mticon.setPixmap(mticonpixmap.scaled(
 gw, gw, Qt.IgnoreAspectRatio,
 Qt.SmoothTransformation))
mticon.setGeometry(width-gw, height-gw, gw, gw)
mticon.clicked.connect(buttonhandler)

datex = QtGui.QLabel(frame1)
datex.setObjectName("datex")
datex.setStyleSheet("#datex { font-family:sans-serif; color: " +
                    ClockConfig.textcolor +
                    "; background-color: transparent; font-size: " +
                    str(int(100 * xscale)) +
                    "px; " +
                    ClockConfig.fontattr +
                    "}")
datex.setAlignment(Qt.AlignCenter)
datex.setWordWrap(True)
datex.setGeometry(10 * xscale, 320 * yscale, 300 * xscale, 300 * yscale)

ypos = 1
wxdesc = QtGui.QLabel(frame1)
wxdesc.setObjectName("wxdesc")
wxdesc.setStyleSheet("#wxdesc { background-color: transparent; color: " +
                     ClockConfig.textcolor +
                     "; font-size: " +
                     str(int(80 * xscale)) +
                     "px; " +
                     ClockConfig.fontattr +
                     "}")
wxdesc.setAlignment(Qt.AlignLeft | Qt.AlignTop)
wxdesc.setGeometry(2 * xscale, ypos * yscale, 750 * xscale, 350 *yscale)
"""
wxicon2 = QtGui.QLabel(frame2)
wxicon2.setObjectName("wxicon2")
wxicon2.setStyleSheet("#wxicon2 { background-color: transparent; }")
wxicon2.setGeometry(0 * xscale, 750 * yscale, 150 * xscale, 150 * yscale)
"""
ypos += 60
temper = QtGui.QLabel(frame1)
temper.setObjectName("temper")
temper.setStyleSheet("#temper { background-color: transparent; color: " +
                     ClockConfig.textcolor +
                     "; font-size: " +
                     str(int(120 * xscale)) +
                     "px; " +
                     ClockConfig.fontattr +
                     "}")
#temper.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
temper.setAlignment(Qt.AlignHCenter)
temper.setGeometry(2 * xscale, ypos * yscale, 420 * xscale, 200)

ypos += 90
wxicon = QtGui.QLabel(frame1)
wxicon.setObjectName("wxicon")
wxicon.setStyleSheet("#wxicon { background-color: transparent; }")
wxicon.setGeometry(50 * xscale, ypos * yscale, 250 * xscale, 200 * yscale)

bottom = QtGui.QLabel(frame1)
bottom.setObjectName("bottom")
bottom.setStyleSheet("#bottom { font-family:sans-serif; color: " +
                     ClockConfig.textcolor +
                     "; background-color: transparent; font-size: " +
                     str(int(90 * xscale)) +
                     "px; " +
                     ClockConfig.fontattr +
                     "}")
bottom.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
bottom.setWordWrap(True)
bottom.setGeometry(20 * xscale, 630 * yscale, 300 * xscale, 250 * yscale)

forecast = []

header1 = QtGui.QLabel(frame2)
header1.setObjectName("header1")
header1.setStyleSheet("#header1 { font-family:sans-serif; color: black" +
                     "; background-color: yellow; font-size: " +
                     str(int(80 * xscale)) +
                     "px; " +
                     ClockConfig.fontattr +
                     "}")
header1.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
header1.setWordWrap(False)
header1.setGeometry(0, 0, width, 80 * yscale)
header1.setText("Előrejelzések")

for i in range(0, 4):
    lab = QtGui.QLabel(frame2)
    lab.setObjectName("forecast" + str(i))
    lab.setStyleSheet("QWidget { background-color: transparent; color: " +
                     ClockConfig.textcolor +
                      "; font-size: " +
                      str(int(50 * xscale)) +
                      "px; " +
                      ClockConfig.fontattr +
                      "}")
    lab.setGeometry(i * 350 * xscale, 90 * yscale,
                    350 * xscale, 590 * yscale)

    icon = QtGui.QLabel(lab)
    icon.setStyleSheet("#icon { background-color: transparent; }")
    icon.setGeometry(0, 0, 150 * xscale, 170 * yscale)
    icon.setObjectName("icon")

    wx = QtGui.QLabel(lab)
    wx.setStyleSheet("#wx { background-color: transparent;}")
    wx.setGeometry(150 * xscale, 10 * yscale, 200 * xscale, 100 * yscale)
    wx.setWordWrap(True)
    wx.setObjectName("wx")

    wx2 = QtGui.QLabel(lab)
    wx2.setStyleSheet("#wx2 { background-color: transparent;font-size: " +
                      str(int(60 * xscale)) +
                      "px; " +
    "}")
    
    wx2.setGeometry(150 * xscale, 120 * yscale, 200 * xscale, 350 * yscale)
    wx2.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    wx2.setWordWrap(True)
    wx2.setObjectName("wx2")

    day = QtGui.QLabel(lab)
    day.setStyleSheet("#day { background-color: transparent; }")
    day.setGeometry(0, 310 * yscale, 350 * xscale, 120 * yscale)
 # nap ora:perc
    day.setAlignment(Qt.AlignRight | Qt.AlignBottom)
    day.setWordWrap(True)
    day.setObjectName("day")

    forecast.append(lab)

header2 = QtGui.QLabel(frame2)
header2.setObjectName("header2")
header2.setStyleSheet("#header2 { font-family:sans-serif; color: black" +
                     "; background-color: yellow; font-size: " +
                     str(int(80 * xscale)) +
                     "px; " +
                     ClockConfig.fontattr +
                     "}")
header2.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
header2.setWordWrap(False)
header2.setGeometry(0, 580 * yscale, width, 80 * yscale)
header2.setText("Szenzorok")

sensorarr = []

for i in range(0, 3):
    lab = QtGui.QLabel(frame2)
    lab.setObjectName("sensor" + str(i))
    lab.setStyleSheet("QWidget { background-color: transparent; color: " +
                     ClockConfig.textcolor +
                      "; font-size: " +
                      str(int(70 * xscale)) +
                      "px; " +
                      ClockConfig.fontattr +
                      "}")
    lab.setGeometry(i * 450 * xscale, 660 * yscale,
                    480 * xscale, 400 * yscale)

    icon = QtGui.QLabel(lab)
    icon.setStyleSheet("#icon { background-color: transparent; }")
    icon.setGeometry(0, 0, 150 * xscale, 170 * yscale)
    icon.setObjectName("icon")

    wx2 = QtGui.QLabel(lab)
    wx2.setStyleSheet("#wx2 { background-color: transparent;font-size: " +
                      str(int(70 * xscale)) +
                      "px; " +
    "}")
    
    wx2.setGeometry(150 * xscale, 40 * yscale, 350 * xscale, 250 * yscale)
    wx2.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    wx2.setWordWrap(True)
    wx2.setObjectName("wx2")

    sensorarr.append(lab)

# Frame 3
header3 = QtGui.QLabel(frame3)
header3.setObjectName("header3")
header3.setStyleSheet("#header3 { font-family:sans-serif; color: black" +
                     "; background-color: yellow; font-size: " +
                     str(int(80 * xscale)) +
                     "px; " +
                     ClockConfig.fontattr +
                     "}")
header3.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
header3.setWordWrap(False)
header3.setGeometry(0, 0, width, 80 * yscale)
header3.setText("Netrádió")

radiotxt = QtGui.QLabel(frame3)
radiotxt.setObjectName("radiotxt")
radiotxt.setStyleSheet("#radiotxt { font-family:sans-serif; color: black" +
                     "; border: 2px solid #7DDBFA; border-radius: 4px; background-color:transparent; color: " +
                     ClockConfig.textcolor +
                      "; font-size: " +
                     str(int(120 * xscale)) +
                     "px; " +
                     ClockConfig.fontattr +
                     "}")
radiotxt.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
radiotxt.setWordWrap(True)
radiotxt.setGeometry(0, 80 * yscale, width, 420 * yscale)
radiotxt.setText("---")

ypos = 550 * yscale

contr = QtGui.QLabel(frame3)
contr.setObjectName("controls")
contr.setStyleSheet("QWidget { background-color: transparent; color: " +
                     ClockConfig.textcolor +
                      "; font-size: " +
                      str(int(70 * xscale)) +
                      "px; " +
                      ClockConfig.fontattr +
                      "}")
c_play = ClickableLabel(contr)
c_play.setStyleSheet("#play { background-color: transparent; }")
c_play.setObjectName("play")
c_playpixmap = QtGui.QPixmap(ClockConfig.icons + "/video-play.png")
gw = c_play.height()*2
contr.setGeometry(0, ypos, width, gw+25)
c_play.setPixmap(c_playpixmap.scaled(
 gw, gw, Qt.IgnoreAspectRatio,
 Qt.SmoothTransformation))
c_play.setGeometry(10, 5, gw, gw)
c_play.clicked.connect(buttonhandler)

#c_up = QtGui.QLabel(frame3)
c_up = ClickableLabel(contr)
c_up.setStyleSheet("#up { background-color: transparent; }")
c_uppixmap = QtGui.QPixmap(ClockConfig.icons + "/up.png")
gw2 = c_up.height()*1.2
c_up.setPixmap(c_uppixmap.scaled(
 gw2, gw2, Qt.IgnoreAspectRatio,
 Qt.SmoothTransformation))
c_up.setGeometry(20 + gw, 0, gw2, gw2)
c_up.setObjectName("up")
c_up.clicked.connect(buttonhandler)

#c_down = QtGui.QLabel(frame3)
c_down = ClickableLabel(contr)
c_down.setStyleSheet("#down { background-color: transparent; }")
c_downpixmap = QtGui.QPixmap(ClockConfig.icons + "/down.png")
#gw2 = c_up.height()
c_down.setPixmap(c_downpixmap.scaled(
 gw2, gw2, Qt.IgnoreAspectRatio,
 Qt.SmoothTransformation))
c_down.setGeometry(20 + gw, gw2 +10, gw2, gw2)
c_down.setObjectName("down")
c_down.clicked.connect(buttonhandler)

radiotxt2 = QtGui.QLabel(contr)
radiotxt2.setObjectName("radiotxt2")
radiotxt2.setStyleSheet("#radiotxt2 { font-family:sans-serif; color: black" +
                     "; border: 2px solid #7DDBFA; border-radius: 4px; background-color:transparent; color: " +
                     ClockConfig.textcolor +
                      "; font-size: " +
                     str(int(70 * xscale)) +
                     "px; " +
                     ClockConfig.fontattr +
                     "}")
radiotxt2.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
txpos = gw+gw2+35
radiotxt2.setGeometry(txpos, 5, width-txpos-5, gw+20)
radiotxt2.setText("Megállítva")

theradio = Radiohandler()

manager = QtNetwork.QNetworkAccessManager()

# proxy = QNetworkProxy()
# proxy.setType(QNetworkProxy.HttpProxy)
# proxy.setHostName("localhost")
# proxy.setPort(8888)
# QNetworkProxy.setApplicationProxy(proxy)

MainTimer = ClockAlarms(ClockConfig.DomoticzURL,ClockConfig.DomoticzUsr,ClockConfig.DomoticzPw,ClockConfig.AlarmScenePrefix,alarmhandler) # DOMOTICZ ADDRESS!!

stimer = QtCore.QTimer()
stimer.singleShot(10, qtstart)

w.show()
if DEBUGMODE!=True:
 w.showFullScreen()
screenstarttime = time.time()
sys.exit(app.exec_())
