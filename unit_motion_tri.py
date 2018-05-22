# Unit for Multisensor
# Purpose: Motion sensor 2PIR+1RADAR data collection
# v1.0
import RPi.GPIO as GPIO

class Motion():
  
 def __init__(self, extcallback, pin_p1, pin_p2=0, pin_r=0):
  self.lastvalue1 = 0
  self.lastvalue2 = 0
  self.lastvalue_p1 = 0
  self.lastvalue_p2 = 0
  self.lastvalue_r = 0
  self.pin_p1 = pin_p1
  self.pin_p2 = pin_p2
  self.pin_r = pin_r
  GPIO.setup(self.pin_p1, GPIO.IN)
  GPIO.add_event_detect(self.pin_p1, GPIO.BOTH, callback=extcallback)
  self.getpinvalues(pin_p1)
  if self.pin_p2 != 0:
   GPIO.setup(self.pin_p2, GPIO.IN)
   GPIO.add_event_detect(self.pin_p2, GPIO.BOTH, callback=extcallback)
   self.getpinvalues(pin_p2)
  if self.pin_r != 0:
   GPIO.setup(self.pin_r, GPIO.IN)
   GPIO.add_event_detect(self.pin_r, GPIO.BOTH, callback=extcallback)
   self.getpinvalues(pin_r)

 def signalhandlerRemove(self):   
   GPIO.remove_event_detect(self.pin_p1)
   if self.pin_p2 != 0:
    GPIO.remove_event_detect(self.pin_p2)
   if self.pin_r != 0:
    GPIO.remove_event_detect(self.pin_r)

 def getpinvalues(self, pin):
   tstat = GPIO.input(pin)
   if (pin == self.pin_p1):
    if self.pin_r == 0:
     self.lastvalue1 = tstat
    else:
     self.lastvalue_p1 = tstat
   if (pin == self.pin_p2) and (self.pin_p2 != 0):
    if self.pin_r == 0:
     self.lastvalue2 = tstat
    else:
     self.lastvalue_p2 = tstat

   if (pin == self.pin_r) and (self.pin_r != 0):
     self.lastvalue_r = tstat

   if self.pin_r != 0:
     if self.lastvalue_r == 1:
      if self.lastvalue_p1 == 1:
       self.lastvalue1 = 1
      if self.lastvalue_p2 == 1:
       self.lastvalue2 = 1
     elif self.lastvalue_r == 0:
      if self.lastvalue_p1 == 0:
       self.lastvalue1 = 0
      if self.lastvalue_p2 == 0:
       self.lastvalue2 = 0
   return self.lastvalue1, self.lastvalue2

 def getlastvalues(self):
   return self.lastvalue1, self.lastvalue2
 
 