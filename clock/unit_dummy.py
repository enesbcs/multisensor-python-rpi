#!/usr/bin/env python
# Unit for Multisensor
# Purpose: Dummy for testing only
# v1.0
import shlex
import math
import util
import time
import random

class BacklightControl():

    BACKLIGHT_CTRL_ENABLED = True

    def __init__(self,pin=18): # default pin 18/PWM0
        if (self.BACKLIGHT_CTRL_ENABLED):
         self.mode = -1
         self.pin = pin
         self._previous_level = 100
         self._current_level = 100

    def __del__(self):
        if (self.BACKLIGHT_CTRL_ENABLED):
         # restore full brightness
         self.set_on()
         print('restored backlight level to full')

    def set_on(self,Force=True):
        if (self.BACKLIGHT_CTRL_ENABLED) and ((self._current_level < 100) or (Force)):
         if (self.mode != 0) or (Force):
          cmd = "gpio -g mode "+str(self.pin)+" out"
          try:
           args = shlex.split(cmd)
           print(args)
           self.mode = 0
          except:
           pass
         cmd = "gpio -g write "+str(self.pin)+" 1"
         try:
          args = shlex.split(cmd)
          print(args)
         except:
          pass
         self._previous_level = self._current_level
         self._current_level = 100

    def set_off(self):
        if (self.BACKLIGHT_CTRL_ENABLED) and (self._current_level > 0):
         if (self.mode != 0):
          cmd = "gpio -g mode "+str(self.pin)+" out"
          args = shlex.split(cmd)
          print(args)
          self.mode = 0
         if (self._current_level) > 0:
          cmd = "gpio -g write "+str(self.pin)+" 0"
          args = shlex.split(cmd)
          print(args)
          self._previous_level = self._current_level
          self._current_level = 0

    def set_level(self,value): # 0-100
       if (self.BACKLIGHT_CTRL_ENABLED):
        if (self._current_level != value):
         self._previous_level = self._current_level
         tv = value
         if tv < 1:
          self.set_off()
         elif tv > 99:
          self.set_on(False)
         else:          
          if (self.mode != 2):
           cmd = "gpio -g mode "+str(self.pin)+" pwm"
           args = shlex.split(cmd)
           print(args)
          self.mode = 2
          self._current_level = tv
          l = round(tv * 10.23)
          cmd = "gpio -g pwm "+str(self.pin)+" "+str(l)
          args = shlex.split(cmd)
          print(args)
         print("Backlight: "+str(self._current_level)) # DEBUG only!

    def set_level_light_compensated(self,lux):
     if lux < 2:
      x = 2
     elif lux > 99:
      x = 100
     else:
      x = lux
     if x >= 50:
      y = (math.log(x) * 100 / math.log(100))
     else: 
      y = (math.log(x/2) * 100 / math.log(100))
     x = math.floor(y/5)*5 
     if x < 5:
      x = 5
     if x > 100:
      x = 100
     self.set_level(x)


    def get_level(self):
        return self._current_level

    def get_previous_level(self):
        return self._previous_level
#!/usr/bin/env python
# Unit for Multisensor
# Purpose: BH1750 data collection
# v1.0

class BH1750():
  
 I2CADDR_BH1750 = 0x23
 I2C_BUS        = 1
 SAMPLE_TIMES   = 4 # ennyi mintabol atlagol
 
 def __init__(self, readinterval=80):
  self.lastvalueread = 0
  self.lastfinalread = time.time()  
  self.prevlht = -100
  self.i2caddr = self.I2CADDR_BH1750
  tst = (readinterval / 3)
  if (tst < 2):
   self.readinterval = 6
   tst = 2
  else:
   self.readinterval = readinterval
  if (tst < self.SAMPLE_TIMES):
   self.sampletime = tst
  else:
   self.sampletime = self.SAMPLE_TIMES    
  self.initialized = True  
  self.resetvalues()

 def resetvalues(self):
  self.LARR = []

 def convertToNumber(self,data):
  return ((data[1] + (256 * data[0])) / 1.2)

 def readvalue(self): # read value from device to inside buffer
  if (self.initialized) and (len(self.LARR) < self.sampletime):
   if ((time.time() - self.lastvalueread) >= 2): # read interval more than 2sec
    try:
     data = random.randint(10, 100)
     self.LARR.append(round(data, 2))
    except:
     data = None 
     self.laststate = 0
    self.lastvalueread = time.time()

 def isValueFinal(self):
   retval = False
   if (len(self.LARR) > 0): 
    if ((time.time() - self.lastfinalread) > self.readinterval):
     retval = True 
   return retval
    
 def readfinalvalue(self): # read value from inside buffer  
   HARR2 = []
   minval = max(self.LARR)*0.5
   for i in range(0,len(self.LARR)):
    if (self.LARR[i] >= minval):
     HARR2.append(self.LARR[i])
   alht = round((sum(HARR2) / len(HARR2)),2)
   self.lastfinalread = time.time()
   self.resetvalues()
   return util.str2num2(alht)

# Unit for Multisensor
# Purpose: CPU thermal info&control
# v1.0

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
   self.pin1 = 0

 def isValueFinal(self):
   retval = False
   if ((time.time() - self.lastfinalread) > self.readinterval):
    retval = True 
   return retval

 def readfinalvalue(self): # read avg value from inside buffer  
   therm = random.randint(30, 50)
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

 def getfanstate(self):
  return self.fanworking

# Unit for Multisensor
# Purpose: Motion sensor (single or combined dual) data collection
# v1.0

class Motion():
  
 def __init__(self, extcallback, pin1, pin2=0):
  self.lastvalue = 0
  self.lastvalue1 = 0
  self.lastvalue2 = 0
  self.pin1 = pin1
  self.pin2 = 0  
  self.getpinvalue(pin1)

 def signalhandlerRemove(self):   
   pass

 def getpinvalue(self, pin):
   tstat = random.randint(0, 1)
   if (pin == self.pin1):
     self.lastvalue1 = tstat
   if (pin == self.pin2):
     self.lastvalue2 = tstat

   if self.pin2 == 0:
     self.lastvalue = tstat
   else:
     if (self.lastvalue == 1): # ha mozgas volt es mindketto nulla akkor off
       if (self.lastvalue1 == 0) and (self.lastvalue2 == 0):
        self.lastvalue = 0

     else:  # ha nem volt mozgas es mindketto 1 akkor on
       if (self.lastvalue1 == 1) and (self.lastvalue2 == 1):
        self.lastvalue = 1

   return self.lastvalue

 def getlastvalue(self):
   return self.lastvalue
 
 #!/usr/bin/env python
# Unit for Multisensor
# Purpose: DHT22 data collection
# v1.0

class DHT():
  
 SAMPLE_TIMES     = 9 # ennyi mintabol atlagol
 
 def __init__(self, pin, readinterval=80):
  self.lastvalueread = 0
  self.lastfinalread = time.time()
  self.prevtemp = -100
  self.prevhum  = -100  
  tst = (readinterval / 3)
  if (tst < 2):
   self.readinterval = 6
   tst = 2
  else:
   self.readinterval = readinterval
  if (tst < self.SAMPLE_TIMES):
   self.sampletime = tst
  else:
   self.sampletime = self.SAMPLE_TIMES    
  self.pin = pin
  self.resetvalues()

 def resetvalues(self):
  self.HARR = []
  self.TARR = []
 
 def readvalue(self): # read value from device to inside buffer
  if (len(self.TARR) < self.sampletime):
   if ((time.time() - self.lastvalueread) >= 2): # read interval more than 2sec
    humidity = random.randint(40, 50)
    temperature = random.randint(20, 25)
    if humidity is not None and temperature is not None:
     self.HARR.append(round(humidity, 2))   
     self.TARR.append(round(temperature, 2))
    self.lastvalueread = time.time()
 
 def isValueFinal(self):
   retval = False
   if ((time.time() - self.lastfinalread) > self.readinterval):
    if (len(self.TARR) > 0): 
     retval = True 
   return retval

 def readfinalvalue(self): # read avg value from inside buffer  
    atemp = 0
    ahum = 0
    if (len(self.TARR) > 0): # initial correction for short arrays
     if (len(self.TARR) == 1):
       atemp = self.TARR[0]
       ahum  = self.HARR[0]
       if (self.prevtemp > -50):
        if (abs(self.prevtemp-atemp) > 4):
         atemp = self.prevtemp
       if (self.prevhum > -50):
        if (abs(self.prevhum-ahum) > 8):
         ahum = self.prevhum
     else:       
      atemp = round((sum(self.TARR) / len(self.TARR)),2)
      ahum = round((sum(self.HARR) / len(self.HARR)),2)
      if ((max(self.TARR) - min(self.TARR)) > 2): # temperature
       if (self.prevtemp < -50):
        self.prevtemp = atemp
       difft = abs(max(self.TARR) - self.prevtemp)
       if (difft > abs(self.prevtemp-min(self.TARR))):
        difft = abs(self.prevtemp-min(self.TARR))
       if (difft < 1):
        difft = 1
       if (difft > 5):
        difft = 5
       TARR2 = []
       for i in range(0,len(self.TARR)):
        if (abs(self.prevtemp-self.TARR[i]) <= difft):
         TARR2.append(self.TARR[i])
       TARR2.append(self.prevtemp)
       atemp = round((sum(TARR2) / len(TARR2)),2)
      if ((max(self.HARR) - min(self.HARR)) > 4): # humidity
       if (self.prevhum < -50):
        self.prevhum = ahum
       diffh = abs(max(self.HARR) - self.prevhum)
       if (diffh > abs(self.prevhum-min(self.HARR))):
        diffh = abs(self.prevhum-min(self.HARR))
       if (diffh < 2):
        diffh = 2
       if (diffh > 8):
        diffh = 8
       HARR2 = []
       for i in range(0,len(self.HARR)):
        if (abs(self.prevhum-self.HARR[i]) <= diffh):
         HARR2.append(self.HARR[i])
       HARR2.append(self.prevhum)
       ahum = round((sum(HARR2) / len(HARR2)),2)
     if (atemp != 0):
      self.prevtemp = atemp
      self.prevhum = ahum
      self.lastfinalread = time.time()
      self.resetvalues()
      #print( str(sum(TARR)) + " " + str(len(TARR)) )
    return util.str2num2(atemp), util.str2num2(ahum)
