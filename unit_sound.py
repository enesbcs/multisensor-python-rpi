# Unit for Multisensor
# Purpose: sound output
# v1.0
# Configuration variables in config_sound.py!
import pygame
import subprocess
import os
import config_sound

SOUND_USER = 0 # 0-nobody, 1-pygame, 2-vlc

def stopVLC():
  global SOUND_USER
  if SOUND_USER == 2:
    os.system("killall vlc")
    SOUND_USER = 0

class Siren():
  
 def __init__(self):
   self.stop()
   self.level = 0
   self.prevlevel = 0  

 def play(self,level): # 0,10,20,30,40,50,60,70
   global SOUND_USER   
   if SOUND_USER == 2:
     stopVLC() # killing VLC with no priority
   else:
    sfx = round(level / 10)
    self.prevlevel = self.level
    if sfx < 1:
      self.stop()
    if (sfx > 0) and (sfx < 8):
      self.level = level
      SOUND_USER = 1
      pygame.mixer.init()
      pygame.mixer.music.load(config_sound.soundfx[sfx-1])
      pygame.mixer.music.play(-1)     
   return True

 def getlevel(self):
   return self.level
   
 def stop(self):
   global SOUND_USER   
   if pygame.mixer.get_init():
    if pygame.mixer.music.get_busy():
     pygame.mixer.music.stop()
    pygame.mixer.quit()
   SOUND_USER = 0 
   self.level = 0   

class Radio():
  
 def __init__(self):
   self.stop()
   self.level = 0
   self.prevlevel = 0  

 def play(self,level):
   global SOUND_USER   
   retval = True
   if SOUND_USER == 1:
    print("Pygame running with priority")
    retval = False
   else:
    sfx = round(level / 10)
    self.prevlevel = self.level
    if SOUND_USER == 2:
      self.stop()
    if (sfx > 0) and (sfx < 7):
      self.level = level
      SOUND_USER = 2
      subprocess.Popen(["/usr/bin/cvlc", config_sound.radiostations[sfx-1][1]])
   return retval  

 def getlevel(self):
   return self.level

 def stop(self):
   stopVLC()
