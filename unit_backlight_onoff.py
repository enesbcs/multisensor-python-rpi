#!/usr/bin/env python
# Unit for Multisensor
# Purpose: HDMI backlight control with relay
# v1.0
# sudoers:
# %adm ALL=(ALL) NOPASSWD: /sbin/rmmod
# %adm ALL=(ALL) NOPASSWD: /sbin/modprobe

import RPi.GPIO as GPIO
import subprocess
import shlex
import math
import os

class BacklightControl():

    BACKLIGHT_CTRL_ENABLED = True

    def __init__(self,pin=18,pin_inverted=False): # default pin 18
        if (self.BACKLIGHT_CTRL_ENABLED):
         self.pin = pin
         self.inverted = pin_inverted
         os.system("DISPLAY=:0.0 xset s noblank && DISPLAY=:0.0 xset s off && DISPLAY=:0.0 xset -dpms")
         if self.pin != 0:
          GPIO.setup(self.pin, GPIO.OUT) # set relay output pin to OUT
         self._current_level = 0
         self.set_on()                   # set to on default

    def __del__(self):
        if (self.BACKLIGHT_CTRL_ENABLED):
         self.set_on()                   # set to on when exit
         print('restored backlight level to full')

    def signalhandlerRemove(self):
        self.__del__()

    def set_on(self):
        if (self.BACKLIGHT_CTRL_ENABLED):
         if self._current_level == 0:
          cmd = "/usr/bin/vcgencmd display_power 1"
          args = shlex.split(cmd)
          out = subprocess.call(args)
          if self.inverted:
           state = 0
          else:
           state = 1
          GPIO.output(self.pin,state)
          cmd = "sudo modprobe ads7846"
          args = shlex.split(cmd)
          out = subprocess.call(args)
          self._current_level = 100

    def set_off(self):
        if (self.BACKLIGHT_CTRL_ENABLED):
         if self._current_level > 0:
          cmd = "sudo rmmod ads7846"
          args = shlex.split(cmd)
          out = subprocess.call(args)
          cmd = "/usr/bin/vcgencmd display_power 0"
          args = shlex.split(cmd)
          out = subprocess.call(args)
          if self.inverted:
           state = 1
          else:
           state = 0
          GPIO.output(self.pin,state)
          self._current_level = 0

    def set_status(self,state):
        if state == 0:
         self.set_off()
        else:
         self.set_on()

    def get_status(self):
        if self._current_level == 0:
         return 0
        else:
         return 1

    def get_level(self):
        return self._current_level

