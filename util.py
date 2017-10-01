# Unit for Multisensor
# Purpose: utility
# v1.0
def str2num(data):
 try:
  data + ''
  return float(data.replace(',','.'))
 except TypeError:
  return data

def str2num2(data):
 return round(str2num(data),2)
