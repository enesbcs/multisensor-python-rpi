#Configuration for presence.py
# Array structure
# 1: W/B: Wifi/Bluetooth type
# 2: MAC address
# 3: Domoticz IDX registered to device with specific MAC
global macmatrix
macmatrix = []
macmatrix.append(['W',"01:02:03:04:05:06", 11])
macmatrix.append(['B',"01:02:03:04:05:07", 22])
# LAN address for nmap scan (for WIFI type)
lan_net = "192.168.1.0/24" 
