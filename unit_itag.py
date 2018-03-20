from bluepy import btle
import threading
import time

ITAG_HANDLE_NAME     = 0x03
ITAG_HANDLE_BATTERY  = 0x08
ITAG_HANDLE_ALARM    = 0x0b
ITAG_HANDLE_KEYPRESS = 0x0e

class BLEEventHandler(btle.DefaultDelegate):
    def __init__(self,keypressed_callback):
        self.keypressed_callback = keypressed_callback
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        if (cHandle==ITAG_HANDLE_KEYPRESS):
         self.keypressed_callback(data[0]) # print("Button pressed")

class BLEBackgroundThread(object):

   def __init__(self,BLEPeripheral,disconn_call,interval=0.5):
    self.interval = interval
    self.enablerun = True
    self.disconn_call = disconn_call
    self.BLEPeripheral = BLEPeripheral
    thread = threading.Thread(target=self.run, args=())
    thread.start()
 
   def run(self):
    while (self.enablerun):
     try:
#       time.sleep(self.interval)
      if self.BLEPeripheral.waitForNotifications(self.interval):
       pass
#     finally:
#      pass
     except:
       self.disconn_call()

   def stoprun(self):
    self.enablerun = False
    
class iTagDevice():
    
   def __init__(self, bleaddr, callbackfunc):
     self.bleaddr = bleaddr
     self.connected = False
     self.callbackfunc = callbackfunc
     x = 2
     while x>0:
       self.connect()
       if self.connected:
        x = 0
       else:
        x -= 1
     if self.check_itag():
#      print("Install callback") # DEBUG
      self.install_callback()
     else:
      self.disconnect()
     if self.connected == False:
      print("Connection failed")

   def isconnected(self):
    return self.connected

   def connect(self):
    connection = True
    try:
     self.BLEPeripheral = btle.Peripheral(self.bleaddr)
    except:
     connection = False
    self.connected = connection

   def install_callback(self):
    if self.connected:
     try:
#      print("setdelegate") # DEBUG
      self.BLEPeripheral.setDelegate( BLEEventHandler(self.callbackfunc) )
#      print("start bg thread") # DEBUG
      self.t = BLEBackgroundThread(self.BLEPeripheral,self.reconnect,0.5)
     except:
       self.reconnect()

   def reconnect(self):
    try:
#     self.__init__(self.bleaddr,self.callbackfunc)
     self.connected = True
     self.BLEPeripheral.connect(self.bleaddr)
#    except Exception as e:
#     print("    ->", e)
#     self.connected = False
#    if self.connected == False:
#     print("FATAL error when trying to reconnect")
    finally:
     time.sleep(1)

   def disconnect(self): 
     self.connected = False
     try:
      self.t.stoprun()
     except:
      pass
     if (self.connected):
      try:
       self.BLEPeripheral.disconnect()
      except:
       pass

   def signalhandlerRemove(self):
    self.disconnect()

   def __exit__(self, type, value, traceback):
    self.disconnect()

   def __del__(self):
    self.disconnect()

   def check_itag(self):
    compat = False
    name = ""
    if (self.connected):
      try:   
       name = self.BLEPeripheral.readCharacteristic(ITAG_HANDLE_NAME)
      except:
       self.reconnect()
    if (name == b'iTAG            '):
     compat = True
    else:
     print("Not supported tag: ",name)
    return compat

   def report_battery(self):
    batt = 0
    battery = 100
    if (self.connected):
      try:   
       battery = self.BLEPeripheral.readCharacteristic(ITAG_HANDLE_BATTERY)
      except:
       self.reconnect()
    if battery:
     batt = battery[0]
    return batt

   def setalarmstate(self,state): # 0=off, 1=on
    if state == 0:
     alarmcmd = b'\0'
    else:
     alarmcmd = b'\1'
    if (self.connected):
      try:   
       blereply = self.BLEPeripheral.writeCharacteristic(ITAG_HANDLE_ALARM,alarmcmd,True)
#       print("Alarm reply:",blereply)
      except:
       self.reconnect()
