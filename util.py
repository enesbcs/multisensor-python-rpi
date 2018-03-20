# Unit for Multisensor
# Purpose: utility
# v1.2
def str2num(data):
 try:
  data + ''
  return float(data.replace(',','.'))
 except TypeError:
  return data

def str2num2(data):
 return round(str2num(data),2)

def rssitodomo(data): # from -30 to -90 convert to 0-11 to Domoticz
 try:
  data = int(data)
 except:
  data = -100
 res = 0
 if data>-90:
  if data>-30:
   res = 11
  else:
   res = int(round((90+data)/5,0)+1)
 if res < 0:
  res = 0
 return res
