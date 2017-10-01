# Unit for Multisensor
# Purpose: Door/window contact
# v1.0
import RPi.GPIO as GPIO

class Door():
  
 def __init__(self, extcallback, pin1):
  self.lastvalue = 0
  self.pin1 = pin1
  GPIO.setup(self.pin1, GPIO.IN, pull_up_down=GPIO.PUD_UP) # for NC
  GPIO.add_event_detect(self.pin1, GPIO.BOTH, callback=extcallback)
  self.getpinvalue(pin1)

 def signalhandlerRemove(self):   
   GPIO.remove_event_detect(self.pin1)

 def getpinvalue(self, pin):
   tstat = GPIO.input(pin)
   if (pin == self.pin1):
     self.lastvalue = tstat
   return self.lastvalue

 def getlastvalue(self):
   return self.lastvalue
