#!/usr/bin/env python
# Unit for Multisensor
# Purpose: Presence detection with WiFi/Bluetooth
# v1.0
# Install nmap:
# sudo apt-get install nmap
# sudo mcedit /etc/sudoers
# %adm ALL=(ALL) NOPASSWD: /usr/bin/nmap
# Install Bluetooth:
# sudo apt-get install bluetooth pi-bluetooth
# Configuration variables in config_presence.py
import subprocess
import shlex
import string
import time
import config_presence

class Presence():
  
 def __init__(self, scantype=1, scaninterval=300):
  self.scantype = scantype         # 1=wifi, 2=blutooth, 3=bluetooth+wifi
  self.scaninterval = scaninterval
  self.lastscan = time.time()
#  self.doScan()
        
 def doScan(self): # returns list of online Domoticz IDX
  pres1 = []
  pres2 = []
  if (self.scantype == 1) or (self.scantype == 3):
     pres1 = self.getonline_wf()
  if (self.scantype > 1):
     pres2 = self.getonline_bt()
  self.lastscan = time.time()     
  return list(set(pres1+pres2))

 def isScanTime(self):
  return ((time.time() - self.lastscan) > self.scaninterval)
  
 def getonline_wf(self):
  onlinelist = []
  cmd = "sudo nmap -n -sP " + config_presence.lan_net
  args = shlex.split(cmd)
  out = subprocess.check_output(args)
  macs = str(out)
  for i in range(len(config_presence.macmatrix)):
   if config_presence.macmatrix[i][0] == 'W':
    if macs.find(config_presence.macmatrix[i][1]) > -1:
     if (config_presence.macmatrix[i][2] in onlinelist) == False:
      onlinelist.append(config_presence.macmatrix[i][2])
  return onlinelist

 def getonline_bt(self):
  onlinelist = []
  cmd = "hcitool scan"
  args = shlex.split(cmd)
  out = subprocess.check_output(args)
  macs = str(out)
  for i in range(len(config_presence.macmatrix)):
   if config_presence.macmatrix[i][0] == 'B':
    if macs.find(config_presence.macmatrix[i][1]) > -1:
     if (config_presence.macmatrix[i][2] in onlinelist) == False:
      onlinelist.append(config_presence.macmatrix[i][2])
  return onlinelist

#pres1 = getonline_wf()
#pres2 = getonline_bt()
#presence = list(set(pres1+pres2))
#for i in range(len(presence)):
# print(presence[i])
