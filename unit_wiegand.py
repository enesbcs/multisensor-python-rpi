# Unit for Wiegand Card Reader
# Purpose: Wiegand card & PIN code reading
# v1.0
import wiegand_io
import RPi.GPIO as GPIO
import threading
import time

class BackgroundThread(object):
   KEYPAD_ESC = 10
   KEYPAD_ENT = 11

   def __init__(self,callbackaddr,interval=0.005):
    self.interval = interval
    self.pin = ""
    self.enablerun = True
    self.callbackfunc = callbackaddr
    thread = threading.Thread(target=self.run, args=())
    thread.start()

   def analyzekey(self,keycode):
        key = int(keycode,2)
#       print("K:",key)
        if (key>=0) and (key<10):
         self.pin = ''.join([self.pin,chr(48+key)])
        elif key == self.KEYPAD_ESC:
         if len(self.pin)>0:
            self.pin = ""      # if PIN entered, delete from buffer
         else:
            self.callbackfunc(1,'ESC') # if no PIN in buffer, send ESC key
        elif key == self.KEYPAD_ENT:
         if len(self.pin)>0:
            self.callbackfunc(2,str(self.pin)) # if PIN buffer not empty, send PIN
            self.pin = ""                      # then clear buffer
         else:
            self.callbackfunc(1,'ENT') # if PIN buffer emtpy, send ENT key

   def run(self):
    while (self.enablerun):
     if (wiegand_io.pendingbitcount() > 0):
      wstr,wbl = wiegand_io.wiegandread()
#      print("Python res:",wstr,wbl)
      if wbl>2 and wbl<5:
       self.analyzekey(wstr)
      elif wbl>6 and wbl<9:
       self.analyzekey(wstr[:4])
       self.analyzekey(wstr[4:8])
      elif wbl > 20:
       self.callbackfunc(3,str(self.binaryToInt(wstr,wbl))) # send Card number as integer
     time.sleep(self.interval)

   def stoprun(self):
    self.enablerun = False

   def binaryToInt(self,binary_string,blen):
                binary_string = binary_string[1:(blen-1)] #Removing the first and last bit (Non-data bits)
                try:
                    result = int(binary_string, 2)
                except:
                    result = 0
                return result

class CardReader():

   def __init__(self, GPIO_D0, GPIO_D1, callbackfunc, GPIO_PWR=0):
     self.GPIO_PWR = GPIO_PWR
     self.tag = ""
     GPIO.setmode(GPIO.BCM)                                                                                                                                 

     wiegand_io.initreader(GPIO_D0,GPIO_D1)

     self.lastpwrchange = time.time()                                                                                                                       
     if GPIO_PWR == 0:                                                                                                                                      
       self.pwrmode = 1                                                                                                                                     
     else:                                                                                                                                                  
       GPIO.setup(self.GPIO_PWR, GPIO.OUT)                                                                                                                  
     self.t = BackgroundThread(callbackfunc,0.01) # 0.005 , 0.01

   def signalhandlerRemove(self):
    self.t.stoprun()

   def setpowermode(self,pwrmode): # 0=off,1=on
     if self.GPIO_PWR == 0:
       self.pwrmode = 1
     elif (pwrmode == 0) or (pwrmode == 1):
       self.pwrmode = pwrmode
       self.lastpwrchange = time.time()
       GPIO.output(self.GPIO_PWR,pwrmode)

   def getpowermode(self): # 0=off,1=on
     if self.GPIO_PWR == 0:
       return 1
     else:
      return self.pwrmode
