#!/usr/bin/python2
# Unit for Multisensor
# Purpose: IR Flame sensor data collection
# v1.0
import time
from datetime import datetime
import Adafruit_ADS1x15
import RPi.GPIO as GPIO
import util

class Flame():
 CALIBARAION_SAMPLE_TIMES     = 15
 CALIBRATION_SAMPLE_INTERVAL  = 100
 READ_SAMPLE_INTERVAL         = 10
 READ_SAMPLE_TIMES            = 5
 ADS1015_I2C_ADDRESS          = 0x48
 I2C_BUS                      = 1
 LOW_LIMIT                    = 13

 def __init__(self, extcallback, pin1, analogPin=1, readinterval=80):
  self.lastvalue = 0
  self.init_ok = True
  self.lastnumvalue = 0
  self.lastalerttime = 0
  self.pin1 = pin1
  self.apin = analogPin
  GPIO.setup(self.pin1, GPIO.IN)
  GPIO.add_event_detect(self.pin1, GPIO.BOTH, callback=extcallback)
  if (readinterval < 2):
   self.readinterval = 2
  else:
   self.readinterval = readinterval 
  self.lastfinalread = time.time()  
  self.calibrationinterval = 600
  self.lastcalibration = 0
  try: 
   self.adc = Adafruit_ADS1x15.ADS1015(address=self.ADS1015_I2C_ADDRESS, busnum=self.I2C_BUS)
  except Exception as e: 
   print('ADS1015 error: ',e)
   self.init_ok = False
   self.readinterval = 99999
  if self.init_ok:
   self.Ro = self.calibration()
   self.getpinvalue(self.pin1) 

 def calibration(self):
  if self.init_ok:
   print("Flame calibration")
   val = 0.0
   for i in range(self.CALIBARAION_SAMPLE_TIMES):
            val += self.adc.read_adc(self.apin,gain=1)
            time.sleep(self.CALIBRATION_SAMPLE_INTERVAL/1000.0)           
   val = val/self.CALIBARAION_SAMPLE_TIMES
   self.lastcalibration = time.time()   
   return val;

 def rawread(self):
  if self.init_ok:
   rs = 0.0
   for i in range(self.READ_SAMPLE_TIMES):
            rs += self.adc.read_adc(self.apin,gain=1)
            time.sleep(self.READ_SAMPLE_INTERVAL/1000.0)
   rs = rs/self.READ_SAMPLE_TIMES
   return rs

 def isValueFinal(self):
  retval = False
  if ((time.time() - self.lastfinalread) > self.readinterval):
    retval = True 
  return retval

 def readfinalvalue(self): # Flameval value
  self.lastfinalread = time.time()   
  val = 0  
  if (self.init_ok):
   read = self.rawread()
   val = 100 - ( read * (100 / self.Ro) )
   if (val < 0):
    val = 0
   if (val > 100):
    val = 100
   self.lastnumvalue = util.str2num2(val)
  return self.lastnumvalue

 def signalhandlerRemove(self):   
   GPIO.remove_event_detect(self.pin1)
   
 def getpinvalue(self, pin):
   tstat = GPIO.input(pin)
   if (pin == self.pin1):
    if (tstat == 1) and (self.lastvalue == 0):
     if ((time.time() - self.lastalerttime) > 2):
      tvalue = self.readfinalvalue()
      self.lastnumvalue = tvalue
      if (tvalue < self.LOW_LIMIT):
       tstat = 0
    self.lastvalue = tstat
    if (tstat == 1):
     self.lastalerttime = time.time()
   return tstat

 def getlastvalue(self): # Flamepin value!
   return self.lastvalue

 def getlastnumvalue(self): # Flameval value!
   return self.lastnumvalue

 def CalibrateSometime(self):
  if ((time.time() - self.lastcalibration) > self.calibrationinterval):
    dethour = int(datetime.now().strftime("%H"))
    if ((dethour > 5) and (dethour < 22)):
      self.Ro = self.calibration()
