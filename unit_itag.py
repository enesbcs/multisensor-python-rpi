from bluepy import btle
import threading
import time

ITAG_UUID_SVC_GENERIC  = "00001800-0000-1000-8000-00805f9b34fb"
ITAG_UUID_NAME         = "00002a00-0000-1000-8000-00805f9b34fb"
ITAG_UUID_SVC_ALARM    = "00001802-0000-1000-8000-00805f9b34fb"
ITAG_UUID_ALARM        = "00002a06-0000-1000-8000-00805f9b34fb"
ITAG_UUID_SVC_BATTERY  = "0000180f-0000-1000-8000-00805f9b34fb"
ITAG_UUID_BATTERY      = "00002a19-0000-1000-8000-00805f9b34fb"
ITAG_UUID_SVC_KEPYRESS = "0000ffe0-0000-1000-8000-00805f9b34fb"
ITAG_UUID_KEYPRESS     = "0000ffe1-0000-1000-8000-00805f9b34fb"

class BLEEventHandler(btle.DefaultDelegate):
    def __init__(self,keypressed_callback,KPHANDLE):
        self.keypressed_callback = keypressed_callback
        self.keypressed_handle = KPHANDLE
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        if (cHandle==self.keypressed_handle):
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
     self.batterychar = None
     self.keypressedhandle = 0
     x = 2
     while x>0:
       self.connect()
       if self.connected:
        x = 0
       else:
        x -= 1
     if self.check_itag():
#      print("Install callback") # DEBUG
      try:
       self.batterychar = self.BLEPeripheral.getCharacteristics(1,0xFF,ITAG_UUID_BATTERY)[0]
#       self.batterychar = self.BLEPeripheral.getServiceByUUID(ITAG_UUID_SVC_BATTERY).getCharacteristics(ITAG_UUID_BATTERY)[0]
      except:
       print("Battery service error")
      try:
       self.alarmchar = self.BLEPeripheral.getServiceByUUID(ITAG_UUID_SVC_ALARM).getCharacteristics(ITAG_UUID_ALARM)[0]
      except:
       print("Alarm service error")
      try:
       kpchar = self.BLEPeripheral.getCharacteristics(1,0xFF,ITAG_UUID_KEYPRESS)[0]
       self.keypressedhandle = kpchar.getHandle()
      except:
       print("Keypress service error")

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
     print("BLE connection error")
    self.connected = connection
    if connection:
     print("BLE connected")

   def install_callback(self):
    if self.connected:
     try:
#      print("setdelegate") # DEBUG
      self.BLEPeripheral.setDelegate( BLEEventHandler(self.callbackfunc,self.keypressedhandle) )
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
#       print("Get Name Characterisctics")
       namechar = self.BLEPeripheral.getServiceByUUID(ITAG_UUID_SVC_GENERIC).getCharacteristics(ITAG_UUID_NAME)[0]
#       print("Read name")
       name = namechar.read().decode("utf-8")
      except:
       self.reconnect()
    if (str(name).upper()[:4] == "ITAG"):
     print("Supported tag: ",str(name))
     compat = True
    else:
     print("Not supported tag: ",str(name))
    return compat

   def report_battery(self):
    batt = 0
    battery = [100]
    if (self.connected):
      try:
       if self.batterychar != None:
        battery = self.batterychar.read()
       else:
        batt = 100
      except:
       self.reconnect()
    if battery:
     batt = battery[0]
    return batt

   def setalarmstate(self,state): # 0=off, 1=on1, 2=on2
    alarmcmd = b'\0'
    if state == 1:
     alarmcmd = b'\1'
    elif state == 2:
     alarmcmd = b'\2'

    if (self.connected):
      try:   
       blereply = self.alarmchar.write(alarmcmd,True)
#       print("Alarm reply:",blereply)
      except:
       self.reconnect()
