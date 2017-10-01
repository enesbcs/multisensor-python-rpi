#!/usr/bin/python2
# Unit for Multisensor
# Purpose: MQ-2 data collection
# v1.0
import time
import Adafruit_ADS1x15
import RPi.GPIO as GPIO
import util

class MQ():
 CALIBARAION_SAMPLE_TIMES     = 15
 CALIBRATION_SAMPLE_INTERVAL  = 100
 READ_SAMPLE_INTERVAL         = 10
 READ_SAMPLE_TIMES            = 5
 ADS1015_I2C_ADDRESS          = 0x48
 I2C_BUS                      = 1
 LOW_LIMIT                    = 13

 def __init__(self, extcallback, pin1, analogPin=0, readinterval=80):
  self.lastvalue = 0
  self.lastnumvalue = 0
  self.lastalerttime = 0
  self.pin1 = pin1
  GPIO.setup(self.pin1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.add_event_detect(self.pin1, GPIO.RISING, callback=extcallback)
  if (readinterval < 2):
   self.readinterval = 2
  else:
   self.readinterval = readinterval 
  self.lastfinalread = time.time()   
  self.calibrationinterval = 50000 
  self.apin = analogPin
  self.initialized = True  
  self.lastcalibration = 0
  try: 
   self.adc = Adafruit_ADS1x15.ADS1015(address=self.ADS1015_I2C_ADDRESS, busnum=self.I2C_BUS)
  except:
   print('ADS1015 error')
   self.initialized = False
   self.readinterval = 99999
  if self.initialized:
   self.Ro = self.calibration()
   self.getpinvalue(pin1) 

 def calibration(self):
  if self.initialized:   
   print("MQ calibration")
   val = 0.0
   for i in range(self.CALIBARAION_SAMPLE_TIMES):
            val += self.adc.read_adc(self.apin,gain=1)
            time.sleep(self.CALIBRATION_SAMPLE_INTERVAL/1000.0)           
   val = val/self.CALIBARAION_SAMPLE_TIMES
   self.lastcalibration = time.time()
   return val;

 def rawread(self):
  if self.initialized:   
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

 def readfinalvalue(self): # mqval value
  self.lastfinalread = time.time()   
  val = 0  
  if self.initialized:      
   read = self.rawread()
   val = ((read - self.Ro) / 4096) * 100
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

 def getlastvalue(self): # mqpin value!
   return self.lastvalue

 def getlastnumvalue(self): # mqval value!
   return self.lastnumvalue

 def CalibrateSometime(self):
  if ((time.time() - self.lastcalibration) > self.calibrationinterval):
     if self.initialized:
      self.Ro = self.calibration()
