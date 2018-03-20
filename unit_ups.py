#!/usr/bin/python2
# Unit for UPS
# Purpose: Battery monitoring through I2C
# v1.0
import time
import math
from datetime import datetime
import Adafruit_ADS1x15
import RPi.GPIO as GPIO
import util

class UPS():
 READ_SAMPLE_INTERVAL         = 0.2
 READ_SAMPLE_TIMES            = 5
 ADS1015_I2C_ADDRESS          = 0x48
 I2C_BUS                      = 1
 BATTERY_DIV                  = 0.0032 # 0.00203 * (4700/(4700+2700))
 PWR_DIV                      = 0.00406 # 0.00203 * (4700/(4700+4700))

 def __init__(self, extcallback, pin1, batCh=0, pwrCh=1, readinterval=30):
  self.lastvalue = 0
  self.lastalerttime = 0
  self.init_ok = True
  self.pin1 = pin1
  self.bch = batCh
  self.pch = pwrCh
  GPIO.setup(self.pin1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # power=1 or 0
  GPIO.add_event_detect(self.pin1, GPIO.BOTH, callback=extcallback)
  if (readinterval < 2):
   self.readinterval = 2
  else:
   self.readinterval = readinterval
  self.lastfinalread = time.time()
  try: 
   self.adc = Adafruit_ADS1x15.ADS1015(address=self.ADS1015_I2C_ADDRESS, busnum=self.I2C_BUS)
  except Exception as e: 
   print('ADS1015 error: ',e)
   self.init_ok = False
   self.readinterval = 99999
  if self.init_ok:
#   print("init ok")
   self.getpinvalue(self.pin1) 

 def rawread(self):
  if self.init_ok:
   rs = 0.0
   rs2 = 0.0
   for i in range(self.READ_SAMPLE_TIMES):
            rs += self.adc.read_adc(self.bch,gain=1)
            time.sleep(self.READ_SAMPLE_INTERVAL)
   for i in range(self.READ_SAMPLE_TIMES):
            rs2 += self.adc.read_adc(self.pch,gain=1)
            time.sleep(self.READ_SAMPLE_INTERVAL)
   rarr = []
   rarr.append(rs/self.READ_SAMPLE_TIMES)
   rarr.append(rs2/self.READ_SAMPLE_TIMES)
   return rarr

 def isValueFinal(self):
  retval = False
  if ((time.time() - self.lastfinalread) > self.readinterval):
    retval = True 
  return retval

 def rawtoresult(self,valtype,val):
  result = 0
  if (valtype == 0): # battery volt
   result = util.str2num2(val * self.BATTERY_DIV)
  if (valtype == 1): # pwr volt
   result = util.str2num2(val * self.PWR_DIV)
  if (valtype == 2): # battery percentage
   result = int(math.ceil(util.str2num2( (( (val * self.BATTERY_DIV)-3.5) * 100) /0.7)))
   if result > 100:
    result = 100
  if (valtype == 3): # battery percentage from volt
   result = int(math.ceil(util.str2num2( ((val-3.5) * 100) /0.7)))
   if result > 100:
    result = 100
  if result < 0:
   result = 0
  return result

 def readfinalvalue(self):
  self.lastfinalread = time.time()
  val = 0
  if (self.init_ok):
   read = self.rawread()
   rarr = []
   bvolt = self.rawtoresult(0,read[0])
   rarr.append(self.rawtoresult(3,bvolt))
   rarr.append(bvolt)
   rarr.append(self.rawtoresult(1,read[1]))
#   print(rarr)
  return rarr

 def signalhandlerRemove(self):
   GPIO.remove_event_detect(self.pin1)

 def getpinvalue(self, pin):
   tstat = GPIO.input(pin)
   if (pin == self.pin1):
    self.lastvalue = tstat
    if (tstat == 0):
     self.lastalerttime = time.time()
   return tstat

 def getlastvalue(self):
   return self.lastvalue

