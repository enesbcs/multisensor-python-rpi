#!/usr/bin/env python
# Unit for Multisensor
# Purpose: DHT22 data collection
# v1.1
import Adafruit_DHT
import time
import util

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
    humidity = None
    temperature = None
    try:
     humidity, temperature = Adafruit_DHT.read(Adafruit_DHT.DHT22, self.pin)
    except:
     humidity = None
     temperature = None
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
    hum = util.str2num2(ahum)
    hstat = 0
    if (hum < 40):
     hstat = 2
    else:
     if (hum < 71):
      hstat = 1
     else:
      hstat = 3
    return util.str2num2(atemp), hum, hstat
