# Unit for Multisensor
# Purpose: Motion sensor (single or combined dual) data collection
# v1.0
import RPi.GPIO as GPIO

class Motion():
  
 def __init__(self, extcallback, pin1, pin2=0):
  self.lastvalue = 0
  self.lastvalue1 = 0
  self.lastvalue2 = 0
  self.pin1 = pin1
  self.pin2 = pin2  
  GPIO.setup(self.pin1, GPIO.IN)
  GPIO.add_event_detect(self.pin1, GPIO.BOTH, callback=extcallback)
  self.getpinvalue(pin1)
  if self.pin2 != 0:
   GPIO.setup(self.pin2, GPIO.IN)
   GPIO.add_event_detect(self.pin2, GPIO.BOTH, callback=extcallback)
   self.getpinvalue(pin2)

 def signalhandlerRemove(self):   
   GPIO.remove_event_detect(self.pin1)
   if self.pin2 != 0:
    GPIO.remove_event_detect(self.pin2)

 def getpinvalue(self, pin):
   tstat = GPIO.input(pin)
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
 
 