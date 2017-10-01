#!/usr/bin/env python
# Unit for Multisensor
# Purpose: BH1750 data collection
# v1.0
import smbus
import util
import time

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
  try: 
   self.bus = smbus.SMBus(self.I2C_BUS)  # Rev 2 Pi uses 1
  except:
   print('I2C error')
   self.initialized = False
   self.readinterval = 99999
  self.resetvalues()

 def resetvalues(self):
  self.LARR = []

 def convertToNumber(self,data):
  return ((data[1] + (256 * data[0])) / 1.2)

 def readvalue(self): # read value from device to inside buffer
  if (self.initialized) and (len(self.LARR) < self.sampletime):
   if ((time.time() - self.lastvalueread) >= 2): # read interval more than 2sec
    try:
     data = self.bus.read_i2c_block_data(self.i2caddr,0x21)
     self.LARR.append(round(self.convertToNumber(data), 2))
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
