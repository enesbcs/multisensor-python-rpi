#!/usr/bin/env python
# Unit for PiClock-MQTT
# Purpose: manage alarm times
# v1.0
import time
import datetime
#from datetime import datetime
import base64
import urllib.request, json 

CHECKPERIOD    = 60 # second
SYNCPERIOD     = 1500 # second
DISKSAVEPERIOD = 43200 # second
JSONFILE       = "timers.json"

# timertype
TIMER_T_BEFORE_SUNRISE = 0
TIMER_T_AFTER_SUNRISE  = 1
TIMER_T_ONTIME         = 2
TIMER_T_BEFORE_SUNSET  = 3
TIMER_T_AFTER_SUNSET   = 4
TIMER_T_FIXED_DATE     = 5

#day
DAY_EVERY    = 0x80
DAY_WEEKDAY  = 0x100
DAY_WEEKEND  = 0x200
DAY_MON      = 0x01
DAY_TUE      = 0x02
DAY_WED      = 0x04
DAY_THU      = 0x08
DAY_FRI      = 0x10
DAY_SAT      = 0x20
DAY_SUN      = 0x40
 
class ClockAlarms():
  
 def __init__(self, domourl, user, password, alarmsceneprefix, alarmhandler_callback, checkperiod=CHECKPERIOD, syncperiod=SYNCPERIOD, disksaveperiod=DISKSAVEPERIOD): # domourl like 'http://domoticz-ip:port"
  self.checkperiod = checkperiod
  self.checkperiodmain = checkperiod
  self.syncperiod = syncperiod
  self.disksaveperiod = disksaveperiod
  self.sceneprefix = alarmsceneprefix
  self.alarmhandler_callback = alarmhandler_callback # call alarm handler if missed alarm detected
  if user != "" and password != "":
   self.urlstart = domourl + "/json.htm?username=" + base64.b64encode(user) + "&password=" + base64.b64encode(password) + "&"
  else:
   self.urlstart = domourl + "/json.htm?"
  self.lastsync = time.time()
  self.lastcheck = self.lastsync
  self.lastalarm = 0
  self.inalarm = False
  self.lastsave = 0
  self.scenearr = [] # 0: sceneidx, 1: scene name, 2 array of alarm devices
  self.timerarr = [] # sceneidx, timeridx, enabled, type, date, hour, minute, days, next epochtime
  if self.checkdomo() == False:
    self.loadfromjson(JSONFILE)  # load from saved json
  else:
    self.readallalarms()
#  self.alarmhandler_callback(1)
  #self.delalarm(2)
#  self.addalarm(2, '10-17-2017', '22', '50', 5, 256)
  
 def readjson(self, fullurl):
   data = []
   try:
    with urllib.request.urlopen(fullurl) as url:
     data = json.loads(url.read().decode())
   except:
    pass
   return data
  
 def checkdomo(self):
  #/json.htm?type=scenes
  # check connection
  # check if sceneidx real
  respstat = False
  jstr = self.readjson(self.urlstart+'type=scenes') # read all scenes
  if (jstr):
   if (jstr['status'] == "OK"):
      self.scenearr = []
      respstat = True
      sc = 0
      try:
       while (jstr['result'][sc]):
        if (jstr['result'][sc]['Name'].startswith(self.sceneprefix)):
         self.scenearr.append([jstr['result'][sc]['idx'],jstr['result'][sc]['Name'],self.getalarmdevices(jstr['result'][sc]['idx'])] )
        sc += 1               
      except:
       pass
  #print(self.scenearr)
  return respstat
 
 def readalarms(self,sceneidx):
  # /json.htm?type=scenetimers&idx=number
  respstat = False
  jstr = self.readjson(self.urlstart+'type=scenetimers&idx='+str(sceneidx)) # read timers for scene
  if (jstr):
    if (jstr['status'] == "OK"):     
      i = 0
      try:
        while (self.timerarr[i]):         
         if int(self.timerarr[i][0]) == int(sceneidx):
          del self.timerarr[i]
         else: 
          i += 1
      except:
       pass
      respstat = True
      sc = 0
      try:
       while (jstr['result'][sc]):
        if ( jstr['result'][sc]['Active'] == "true" ):
          t_en = 1
        else:
          t_en = 0
        if t_en == 1:  
         timearr = jstr['result'][sc]['Time'].split(":")
         self.timerarr.append([ sceneidx, jstr['result'][sc]['idx'], t_en, jstr['result'][sc]['Type'], jstr['result'][sc]['Date'], timearr[0], timearr[1], jstr['result'][sc]['Days'],
          self.timeencode(jstr['result'][sc]['Date'],timearr[0],timearr[1],jstr['result'][sc]['Type'],jstr['result'][sc]['Days'])  ]) 
        sc += 1       
      except:
       pass
# sceneidx, timeridx list  
  return respstat

 def readallalarms(self):
   respstat = False
   self.timerarr = []
   for i in range(len(self.scenearr)):
    respstat = self.readalarms(self.scenearr[i][0])
   return respstat 
    
 def getalarmdevices(self,sceneidx):
 #  List devices in a scene
 #/json.htm?type=command&param=getscenedevices&idx=number&isscene=true
 # sceneidx, deviceidx
   jstr = self.readjson(self.urlstart+'type=command&param=getscenedevices&isscene=true&idx='+sceneidx)
   devlist = []
   if (jstr):
    if (jstr['status'] == "OK"):
      sc = 0
      try:
       while (jstr['result'][sc]):
        devlist.append(jstr['result'][sc]['DevID'])
        sc += 1       
      except:
       pass
   return devlist
 
 def timeencode(self, tdate, thour, tmin, ttype, tdaycode): #tdaycode skip if fixed_date
   tvdate = ""
   tvdow = int(time.strftime("%w"))
   diff = [365]
   if ttype == TIMER_T_FIXED_DATE:
    if tdate != "":      
     t1 = datetime.datetime.strptime(tdate +" "+str(thour)+":"+str(tmin), "%m-%d-%Y %H:%M")
     t2 = datetime.datetime.strptime(datetime.datetime.now().strftime("%m-%d-%Y %H:%M"), "%m-%d-%Y %H:%M")     
     if (t1 > t2):                 
      diff.append(0)
      tvdate = tdate
   if ttype == TIMER_T_ONTIME:
     t1 = datetime.datetime.strptime(str(thour)+":"+str(tmin), "%H:%M")
     t2 = datetime.datetime.strptime(time.strftime("%H")+":"+time.strftime("%M"),"%H:%M")
     if (t1 > t2):
       tvdate = time.strftime("%m-%d-%Y")
     else:
       tvdate = time.strftime("%m-") + str(int(time.strftime("%d"))+1) + time.strftime("-%Y")              
       tvdow += 1
       if tvdow > 6:
        tvdow = 0
  
     if (tdaycode & DAY_EVERY) == DAY_EVERY:
        diff.append(0)
     elif (tdaycode & DAY_WEEKDAY) == DAY_WEEKDAY:
        if tvdow == 0:
         diff.append(1)
        elif tvdow == 6:
         diff.append(2)
        else:
         diff.append(0)
     elif (tdaycode & DAY_WEEKEND) == DAY_WEEKEND:
        if (tvdow == 0) or (tvdow == 6):
         diff.append(0)
        else:
         diff.append(6 - tvdow)
     else:    
      if (tdaycode & DAY_SUN) == DAY_SUN:
        if (tvdow == 0):
         diff.append(0)
        else:
         diff.append(7 - tvdow)
      if (tdaycode & DAY_MON) == DAY_MON:
        if (tvdow == 1):
         diff.append(0)
        if tvdow == 0:
         diff.append(1)
        else:
         diff.append(8 - tvdow)
      if (tdaycode & DAY_TUE) == DAY_TUE:
        if (tvdow == 2):
         diff.append(0)
        if tvdow < 2:
         diff.append(2)
        else:
         diff.append(9 - tvdow)
      if (tdaycode & DAY_WED) == DAY_WED:
        if (tvdow == 3):
         diff.append(0)
        if tvdow < 3:
         diff.append(3 - tvdow)
        else:
         diff.append(10 - tvdow)
      if (tdaycode & DAY_THU) == DAY_THU:
        if (tvdow == 4):
         diff.append(0)
        if tvdow < 4:
         diff.append(4 - tvdow)
        else:
         diff.append(11 - tvdow)
      if (tdaycode & DAY_FRI) == DAY_FRI:
        if (tvdow == 5):
         diff.append(0) 
        if tvdow < 5:
         diff.append(5 - tvdow)
        else:
         diff.append(12 - tvdow)
      if (tdaycode & DAY_SAT) == DAY_SAT:
        if (tvdow == 5):
         diff.append(0) 
        if tvdow < 5:
         diff.append(5 - tvdow)
        else:
         diff.append(12 - tvdow)

   ndiff = min(diff)
   if ndiff < 180:
    if ndiff > 6:
     ndiff -= 7
    if ndiff > 0:
     cdate = tvdate.split("-")
     tvdate = cdate[0] + "-" + str(int(cdate[1])+ndiff) + "-" + cdate[2]
    cdate = tvdate.split("-") 
    tt = time.struct_time((int(cdate[2]),int(cdate[0]),int(cdate[1]),int(thour),int(tmin),1,0,0,-1))
    resultdt = time.mktime(tt)
   else:
    resultdt = 0   
#   print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(resultdt)) )
   return resultdt
   
 def addalarm(self,sceneidx, pdate, phour, pmin, pttype, pdays): #HH:mm time, active days, repeat?
  # /json.htm?type=command&param=addscenetimer&idx=number&active=&timertype=&date=&hour=&min=&randomness=&command=&level=&days=
#sceneidx, timeridx, enabled, timertype, hour, min, days
#/json.htm?type=command&param=updatescenetimer&idx=" + idx +&active=&timertype=&date=&hour=&min=&randomness=&command=&level=&days=
  respstat = False 
  jstr = self.readjson(self.urlstart+'type=command&param=addscenetimer&idx='+str(sceneidx)+'&active=true&randomness=false&command=0&level=100&timertype='+str(pttype)+'&date='+str(pdate)+'&hour='+str(phour)+'&min='+str(pmin)+'&days='+str(pdays) )
  if (jstr):
   if (jstr['status'] == "OK"):
    respstat = self.readalarms(sceneidx)    
  if respstat == False: # offline mode
   self.timerarr.append([ sceneidx, '1', 1, pttype, pdate, phour, pmin, pdays,
          self.timeencode(pdate,phour,pmin,pttype,pdays)  ]) 
  return respstat

 def updatealarm(self, timeridx, pdate, phour, pmin, pttype, pdays): #HH:mm time, active days, repeat?
  # /json.htm?type=command&param=addscenetimer&idx=number&active=&timertype=&date=&hour=&min=&randomness=&command=&level=&days=
#sceneidx, timeridx, enabled, timertype, hour, min, days
#/json.htm?type=command&param=updatescenetimer&idx=" + idx +&active=&timertype=&date=&hour=&min=&randomness=&command=&level=&days=
  respstat = False 
  sceneidx = 0
  jstr = self.readjson(self.urlstart+'type=command&param=updatescenetimer&idx='+str(timeridx)+'&active=true&randomness=false&command=0&level=100&timertype='+str(pttype)+'&date='+str(pdate)+'&hour='+str(phour)+'&min='+str(pmin)+'&days='+str(pdays) )
  if (jstr):
   if (jstr['status'] == "OK"):
    for j in range(len(self.timerarr)):
     if int(self.timerarr[j][1]) == int(timeridx):       
      sceneidx = self.timerarr[j][0]
    time.sleep(1)
    respstat = self.readalarms(sceneidx)
  if respstat == False: # offline mode
   newentry = True
   for i in range(len(self.timerarr)):
    if int(self.timerarr[i][1]) == int(timeridx):
     newentry = False
     self.timerarr[i][3] = pttype
     self.timerarr[i][4] = pdate
     self.timerarr[i][5] = phour
     self.timerarr[i][6] = pmin
     self.timerarr[i][7] = pdays
     self.timerarr[i][8] = self.timeencode(pdate,phour,pmin,pttype,pdays)
   if newentry:  
    if int(sceneidx) < 1:
     sceneidx = 1   
    self.timerarr.append([ sceneidx, '1', 1, pttype, pdate, phour, pmin, pdays,
          self.timeencode(pdate,phour,pmin,pttype,pdays)  ]) 
  return respstat

 def delalarm(self,timeridx):
#"json.htm?type=command&param=deletescenetimer&idx=" + idx,
  respstat = False
  for i in range(len(self.timerarr)):
   if int(self.timerarr[i][1]) == int(timeridx):
     del self.timerarr[i]
     break
  jstr = self.readjson(self.urlstart+'type=command&param=deletescenetimer&idx='+str(timeridx)) # delete scene
  if (jstr):
   if (jstr['status'] == "OK"):
    respstat = True
  return respstat

 def getalarmlist(self):
  return self.timerarr   

 def getscenelist(self):
  return self.scenearr
 
 def checktimeractivities(self): 
  timernear = 0
  for i in range(len(self.timerarr)):
    if int(self.timerarr[i][2]) == 1:
      tdiff = self.timerarr[i][8] - time.time()
      if (tdiff < (self.checkperiodmain*5)) and (tdiff >0):
        timernear = 1 
      if (tdiff < 0) and (tdiff > -70):
        if (self.inalarm == False) and ((time.time() - self.lastalarm) > 80):
         print("Forcing alarm!")
         self.alarmhandler_callback(1)  # send back alarm state to main program        
         if self.inalarm == False:
          self.alarmstarted()           # set alarm state
  if timernear == 1:     
   if self.checkperiodmain == self.checkperiod:
    self.checkperiod = 10
  else:
   if self.checkperiodmain != self.checkperiod:
    self.checkperiod = self.checkperiodmain 
  self.lastcheck = time.time() 
   
 def schedulesync(self): 
  # download all alarm times & save alarm times to json?
  if self.checkdomo():
    self.readallalarms()
  if ((time.time() - self.lastsave) > self.disksaveperiod):
   self.savetojson(JSONFILE)
   self.lastsave = time.time()  
  self.lastsync = time.time()
  
 def loadfromjson(self,jfile):
  success = True
  try:
   with open(jfile, "r") as infile:
    self.timerarr = json.load(infile)
  except:
    succes = False
  return success

 def savetojson(self, jfile):  
  success = True
  try:
   with open(jfile, "w") as outfile:
    json.dump(self.timerarr, outfile)
  except:
    succes = False
  return success
 
 def TimerPeriodicCheck(self): # call from main program loop
   if ((time.time() - self.lastcheck) > self.checkperiod):
     self.checktimeractivities()
     if ((time.time() - self.lastsync) > self.syncperiod):
      self.schedulesync()
 
 def alarmstarted(self): # call from main program if specific mqtt device turned on
  self.lastalarm = time.time()
  self.inalarm = True
  
 def alarmstopped(self): # call from main program if specific mqtt device turned off
  self.inalarm = False

 def isalarmactive(self): # call from main program to monitor alarm state
  return self.inalarm
