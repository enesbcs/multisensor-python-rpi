#!/usr/bin/env python
# Unit for Multisensor
# Purpose: LCD backlight control with PWM
# v1.0
import wiringpi as gpio # not used directly, PiWiringPi is buggy as hell
import subprocess
import shlex
import math

class BacklightControl():

    BACKLIGHT_CTRL_ENABLED = True

    def __init__(self,pin=18): # default pin 18/PWM0
        if (self.BACKLIGHT_CTRL_ENABLED):
         self.prevlux = 100
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
          args = shlex.split(cmd)
          out = subprocess.call(args)
          self.mode = 0
         cmd = "gpio -g write "+str(self.pin)+" 1"
         args = shlex.split(cmd)
         out = subprocess.call(args)
         self._previous_level = self._current_level
         self._current_level = 100

    def set_off(self):
        if (self.BACKLIGHT_CTRL_ENABLED) and (self._current_level > 0):
         if (self.mode != 0):
          cmd = "gpio -g mode "+str(self.pin)+" out"
          args = shlex.split(cmd)
          out = subprocess.call(args)
          self.mode = 0
         if (self._current_level) > 0:
          cmd = "gpio -g write "+str(self.pin)+" 0"
          args = shlex.split(cmd)
          out = subprocess.call(args)
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
           out = subprocess.call(args)
           self.mode = 2
          self._current_level = tv
          l = round(tv * 10.23)
          cmd = "gpio -g pwm "+str(self.pin)+" "+str(l)
          args = shlex.split(cmd)
          out = subprocess.call(args)
         print("Backlight: "+str(self._current_level)) # DEBUG only!

    def set_level_light_compensated(self,lux):
     if lux == 65535:
      lux = self.prevlux
     else:
      self.prevlux = lux
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
