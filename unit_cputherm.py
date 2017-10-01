# Unit for Multisensor
# Purpose: CPU thermal info&control
# v1.0
import RPi.GPIO as GPIO
import util
import time
import os

class CPUThermal():
  
 FAN_THERMAL_ON    = 49 # fan on Celsius
 FAN_THERMAL_OFF   = 46 # fan off Celsius
 FAN_COOLDOWN_TIME = 120 # fan on/off cooldown time in sec
 FAN_MAX_TIME      = 1500 # fan max working time in sec
 
 def __init__(self, pin1=0, readinterval=80):
   self.lastvalue = 0
   self.fanworking = 0
   self.lastfinalread = time.time()      
   self.fanstart = 0
   if (readinterval < 2):
    self.readinterval = 2
   else:
    self.readinterval = readinterval  
   self.pin1 = pin1   
   if self.pin1 != 0:
    GPIO.setup(self.pin1, GPIO.OUT)  

 def isValueFinal(self):
   retval = False
   if ((time.time() - self.lastfinalread) > self.readinterval):
    retval = True 
   return retval

 def readfinalvalue(self): # read avg value from inside buffer  
   res = os.popen('vcgencmd measure_temp').readline()
   therm = util.str2num2(res.replace('temp=','').replace("'C\n",""))
   self.lastfinalread = time.time()   
   if self.pin1 != 0:
    if (therm > self.FAN_THERMAL_ON):
     if (self.fanworking == 0):
      if (round((time.time() - self.fanstart),1)  > self.FAN_COOLDOWN_TIME):
       self.fancontrol(1)
    if (self.fanworking == 1):
     if (therm < self.FAN_THERMAL_OFF):
      if (round((time.time() - self.fanstart),1) > self.FAN_COOLDOWN_TIME):
       self.fancontrol(0)
     if (round((time.time() - self.fanstart),1) > self.FAN_MAX_TIME):       
       self.fancontrol(0)
       self.fanstart = time.time()       
   return therm
 
 def fancontrol(self,state):
   if self.pin1 != 0:   
    if (self.fanworking != state):
     self.fanworking = state
     if (state == 1):
      self.fanstart = time.time()
     GPIO.output(self.pin1,state)

 def getfanstate(self):
  return self.fanworking
