# Unit for Multisensor
# Purpose: CPU thermal info&control - Orange Pi
# v1.1
from pyA20.gpio import gpio
import util
import time
import os

class CPUThermal():
  
 FAN_THERMAL_ON    = 65 # fan on Celsius
 FAN_THERMAL_OFF   = 41 # fan off Celsius
 FAN_COOLDOWN_TIME = 120 # fan on/off cooldown time in sec
 FAN_MAX_TIME      = 1500 # fan max working time in sec
 CPUCORE_MANAGEMENT = 1 # enabled
 CPU_USAGE_LIMIT   = 80 # percentage
 
 def __init__(self, pin1=0, readinterval=80, readrssi=False):
   self.lastvalue = 0
   self.fanworking = 0
   self.lastfinalread = time.time()
   self.fanstart = 0
   self.readrssi = readrssi
   if (readinterval < 2):
    self.readinterval = 2
   else:
    self.readinterval = readinterval  
   self.pin1 = pin1
   if self.pin1 != 0:  # 6 = PA06/pin7
    gpio.init()
    gpio.setcfg(self.pin1, gpio.OUTPUT)
    self.fanworking = gpio.input(self.pin1)

 def isValueFinal(self):
   retval = False
   if ((time.time() - self.lastfinalread) > self.readinterval):
    retval = True 
   return retval

 def readfinalvalue(self): # read avg value from inside buffer  
   therm = []
   therm2 = self.read_cpu_temp()
   therm.append(therm2)
   cpusage = self.read_cpu_usage()
   therm.append(cpusage)

   if self.CPUCORE_MANAGEMENT == 1:
    if cpusage < self.CPU_USAGE_LIMIT:
#     print("Reduce power")
     for i in range(3,0,-1):
      if self.get_cpucore_state(i) == "1":
       self.set_cpucore_state(i,0)
       print("Core",i," off")
       break
    else:
#     print("Increase power")
     for i in range(1,4,1):
      if self.get_cpucore_state(i) == "0":
       self.set_cpucore_state(i,1)
       print("Core",i," on")
       break

   if self.readrssi:
    try:
     res = os.popen("/bin/cat /proc/net/wireless | awk 'NR==3 {print $4}' | sed 's/\.//'").read().strip()
    except:
     res = "-30"
#    print(res)
    therm.append(res)

   self.lastfinalread = time.time()
   if self.pin1 != 0:
    if (therm2 > self.FAN_THERMAL_ON):
     if (self.fanworking == 0):
      if (round((time.time() - self.fanstart),1)  > self.FAN_COOLDOWN_TIME):
       self.fancontrol(1)
    if (self.fanworking == 1):
     if (therm2 < self.FAN_THERMAL_OFF):
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
     gpio.output(self.pin1,state)

 def getfanstate(self):
  return self.fanworking

 def read_cpu_temp(self):
  try:
   res = os.popen('cat /sys/devices/virtual/thermal/thermal_zone0/temp').readline()
  except:
   res = "0"
  therm2 = util.str2num2(res)
  if therm2 > 300:
   therm2 = util.str2num2(therm2 /1000)
  return therm2

 def read_cpu_usage(self):
  try:
   cpu_a_prev = round(float(os.popen('''grep 'cpu ' /proc/stat | awk '{usage=($1+$2+$3+$7+$8)} END {print usage }' ''').readline()),2)
   cpu_t_prev = round(float(os.popen('''grep 'cpu ' /proc/stat | awk '{usage=($1+$2+$3+$7+$8+$4+$5)} END {print usage }' ''').readline()),2)
  except:
   cpu_a_prev = 0
   cpu_t_prev = 0
  time.sleep(0.5)
  try:
   cpu_a_cur = round(float(os.popen('''grep 'cpu ' /proc/stat | awk '{usage=($1+$2+$3+$7+$8)} END {print usage }' ''').readline()),2)
   cpu_t_cur = round(float(os.popen('''grep 'cpu ' /proc/stat | awk '{usage=($1+$2+$3+$7+$8+$4+$5)} END {print usage }' ''').readline()),2)
  except:
   cpu_a_cur = 0
   cpu_t_cur = 1
  cpu_util = util.str2num2(100*(cpu_a_cur-cpu_a_prev) / (cpu_t_cur-cpu_t_prev))
  return cpu_util

 def set_cpucore_state(self,num,state):
  cmdstr = "echo "+str(state)+" >/sys/devices/system/cpu/cpu"+str(num)+"/online"
  try:
   res = os.popen(cmdstr)
  except:
   pass

 def get_cpucore_state(self,num):
  cmdstr = "cat /sys/devices/system/cpu/cpu"+str(num)+"/online"
  try:
   res = str(os.popen(cmdstr).readline()).strip()
  except:
   res = "0"
  return res
