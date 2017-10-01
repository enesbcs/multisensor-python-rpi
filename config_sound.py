#Configuration for unit_sound.py
# Array structure
# 1: relative path of wav files
global soundfx
soundfx = []
soundfx.append("sound/ring.wav") # 10 csengo https://www.youtube.com/watch?v=-2tAjph87UU 0:55
soundfx.append("sound/bell.wav") # 20 harang https://www.youtube.com/watch?v=-2tAjph87UU 0:14
soundfx.append("sound/delay.wav") # 30 kesleltetes
soundfx.append("sound/alarm.wav") # 40 behat riasztas
soundfx.append("sound/fire.wav") # 50 tuz riasztas
soundfx.append("sound/water.wav") # 60 viz riasztas https://www.youtube.com/watch?v=0IvuUBfwVPw
soundfx.append("sound/CO.wav") # 70 gaz riasztas

#1=url
#2=name
global radiostations
radiostations = []
radiostations.append(["CsabaRádió","http://online.csabaradio.hu:8000/128kbps"])
radiostations.append(["Rádió1","http://myonlineradio.hu/radio1.php#.mp3"])
radiostations.append(["InfoRádió","http://79.172.209.223:8400/stream"])
radiostations.append(["MusicFM","http://stream.musicfm.hu:8000/musicfm.mp3"])
radiostations.append(["SlágerFM","http://92.61.114.159:7812/slagerfm256.mp3"])
radiostations.append(["ClassFM","http://icast.connectmedia.hu/4784/live.mp3"])
