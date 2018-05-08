#!/usr/bin/env python
# Unit for Multisensor
# Purpose: AM2320 data collection
# v1.0
import time
import posix
from fcntl import ioctl
import util

class AM2320:
  I2C_ADDR = 0x5c
  I2C_SLAVE = 0x0703 

  def __init__(self, i2cbus = 1):
    self._i2cbus = i2cbus

  @staticmethod
  def _calc_crc16(data):
    crc = 0xFFFF
    for x in data:
      crc = crc ^ x
      for bit in range(0, 8):
        if (crc & 0x0001) == 0x0001:
          crc >>= 1
          crc ^= 0xA001
        else:
          crc >>= 1
    return crc

  @staticmethod
  def _combine_bytes(msb, lsb):
    return msb << 8 | lsb


  def readSensor(self):
    fd = posix.open("/dev/i2c-%d" % self._i2cbus, posix.O_RDWR)

    ioctl(fd, self.I2C_SLAVE, self.I2C_ADDR)
  
    # wake AM2320 up, goes to sleep to not warm up and affect the humidity sensor 
    # This write will fail as AM2320 won't ACK this write
    try:
      posix.write(fd, b'\0x00')
    except:
      pass
    time.sleep(0.001)  #Wait at least 0.8ms, at most 3ms
  
    # write at addr 0x03, start reg = 0x00, num regs = 0x04 */  
    try:
     posix.write(fd, b'\x03\x00\x04')
    except:
     return (None,None)
    time.sleep(0.0016) #Wait at least 1.5ms for result
    # Read out 8 bytes of result data
    # Byte 0: Should be Modbus function code 0x03
    # Byte 1: Should be number of registers to read (0x04)
    # Byte 2: Humidity msb
    # Byte 3: Humidity lsb
    # Byte 4: Temperature msb
    # Byte 5: Temperature lsb
    # Byte 6: CRC lsb byte
    # Byte 7: CRC msb byte
    data = bytearray(posix.read(fd, 8))

    # Check data[0] and data[1]
    if data[0] != 0x03 or data[1] != 0x04:
      raise Exception("First two read bytes are a mismatch")

    # CRC check
    if self._calc_crc16(data[0:6]) != self._combine_bytes(data[7], data[6]):
      raise Exception("CRC failed")
    
    # Temperature resolution is 16Bit, 
    # temperature highest bit (Bit15) is equal to 1 indicates a
    # negative temperature, the temperature highest bit (Bit15)
    # is equal to 0 indicates a positive temperature; 
    # temperature in addition to the most significant bit (Bit14 ~ Bit0)
    # indicates the temperature sensor string value.
    # Temperature sensor value is a string of 10 times the
    # actual temperature value.
    temp = self._combine_bytes(data[4], data[5])
    if temp & 0x8000:
      temp = -(temp & 0x7FFF)
    temp /= 10.0

    humi = self._combine_bytes(data[2], data[3]) / 10.0

    return (temp, humi)  

class TEMP():
  
 SAMPLE_TIMES     = 9 # ennyi mintabol atlagol
 
 def __init__(self, readinterval=80):
  self.lastvalueread = 0
  self.lastfinalread = time.time()
  self.prevtemp = -100
  self.prevhum  = -100  
  tst = (readinterval / 3)
  if (tst < 2):
   self.readinterval = 6
   tst = 2
  else:
   self.readinterval = readinterval
  if (tst < self.SAMPLE_TIMES):
   self.sampletime = tst
  else:
   self.sampletime = self.SAMPLE_TIMES    
  self.resetvalues()

 def resetvalues(self):
  self.HARR = []
  self.TARR = []
 
 def readvalue(self): # read value from device to inside buffer
  if (len(self.TARR) < self.sampletime):
   if ((time.time() - self.lastvalueread) >= 3): # read interval more than 2sec
    humidity = None
    temperature = None
    amdev = AM2320(1)
    try:
     temperature, humidity = amdev.readSensor()
    except:
     humidity = None
     temperature = None
    if humidity is not None and temperature is not None:
     self.HARR.append(round(humidity, 2))
     self.TARR.append(round(temperature, 2))
    self.lastvalueread = time.time()
#    print(humidity,temperature)

 def isValueFinal(self):
   retval = False
   if ((time.time() - self.lastfinalread) > self.readinterval):
    if (len(self.TARR) > 0): 
     retval = True 
   return retval

 def readfinalvalue(self): # read avg value from inside buffer  
    atemp = 0
    ahum = 0
    if (len(self.TARR) > 0): # initial correction for short arrays
     if (len(self.TARR) == 1):
       atemp = self.TARR[0]
       ahum  = self.HARR[0]
       if (self.prevtemp > -50):
        if (abs(self.prevtemp-atemp) > 4):
         atemp = self.prevtemp
       if (self.prevhum > -50):
        if (abs(self.prevhum-ahum) > 8):
         ahum = self.prevhum
     else:       
      atemp = round((sum(self.TARR) / len(self.TARR)),2)
      ahum = round((sum(self.HARR) / len(self.HARR)),2)
      if ((max(self.TARR) - min(self.TARR)) > 2): # temperature
       if (self.prevtemp < -50):
        self.prevtemp = atemp
       difft = abs(max(self.TARR) - self.prevtemp)
       if (difft > abs(self.prevtemp-min(self.TARR))):
        difft = abs(self.prevtemp-min(self.TARR))
       if (difft < 1):
        difft = 1
       if (difft > 5):
        difft = 5
       TARR2 = []
       for i in range(0,len(self.TARR)):
        if (abs(self.prevtemp-self.TARR[i]) <= difft):
         TARR2.append(self.TARR[i])
       TARR2.append(self.prevtemp)
       atemp = round((sum(TARR2) / len(TARR2)),2)
      if ((max(self.HARR) - min(self.HARR)) > 4): # humidity
       if (self.prevhum < -50):
        self.prevhum = ahum
       diffh = abs(max(self.HARR) - self.prevhum)
       if (diffh > abs(self.prevhum-min(self.HARR))):
        diffh = abs(self.prevhum-min(self.HARR))
       if (diffh < 2):
        diffh = 2
       if (diffh > 8):
        diffh = 8
       HARR2 = []
       for i in range(0,len(self.HARR)):
        if (abs(self.prevhum-self.HARR[i]) <= diffh):
         HARR2.append(self.HARR[i])
       HARR2.append(self.prevhum)
       ahum = round((sum(HARR2) / len(HARR2)),2)
     if (atemp != 0):
      self.prevtemp = atemp
      self.prevhum = ahum
      self.lastfinalread = time.time()
      self.resetvalues()
#      print( str(sum(self.TARR)) + " " + str(len(self.TARR)) )
    hum = util.str2num2(ahum)
    hstat = 0
    if (hum < 40):
     hstat = 2
    else:
     if (hum < 71):
      hstat = 1
     else:
      hstat = 3
    return util.str2num2(atemp), hum, hstat
