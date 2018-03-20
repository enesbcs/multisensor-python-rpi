primary_coordinates = 46.61797817, 21.0793229  # Change to your Lat/Lon

wuprefix = 'http://api.wunderground.com/api/'
background = 'clock/images/wood.jpg'
squares1 = 'clock/images/squares1-jean.png'
squares2 = 'clock/images/squares2-blue.png'
icons = 'clock/icons-lightblue'
#textcolor = '#bef'
textcolor = 'white'
clockface = 'clock/images/clockface3.png'
hourhand = 'clock/images/hourhand.png'
minhand = 'clock/images/minhand.png'
sechand = 'clock/images/sechand.png'

digital = 0             # 1 = Digtal Clock, 0 = Analog Clock

# Goes with light blue config (like the default one)
digitalcolor = "#50CBEB"
digitalformat = "{0:%H:%M\n%S}"  # The format of the time
digitalsize = 400
# The above example shows in this way:
#  https://github.com/n0bel/PiClock/blob/master/Documentation/Digital%20Clock%20v1.jpg
# ( specifications of the time string are documented here:
#  https://docs.python.org/2/library/time.html#time.strftime )

# digitalformat = "{0:%I:%M}"
# digitalsize = 250
#  The above example shows in this way:
#  https://github.com/n0bel/PiClock/blob/master/Documentation/Digital%20Clock%20v2.jpg


metric = 1  # 0 = English, 1 = Metric
weather_refresh = 30    # minutes
# gives all text additional attributes using QT style notation
# example: fontattr = 'font-weight: bold; '
fontattr = ''

# These are to dim the radar images, if needed.
# see and try Config-Example-Bedside.py
#dimcolor = QColor('#000000')
#dimcolor.setAlpha(0)

# Language Specific wording
# Weather Undeground Language code
#  (https://www.wunderground.com/weather/api/d/docs?d=language-support&MR=1)
wuLanguage = "HU"

# The Python Locale for date/time (locale.setlocale)
#  '' for default Pi Setting
# Locales must be installed in your Pi.. to check what is installed
# locale -a
# to install locales
# sudo dpkg-reconfigure locales
DateLocale = 'hu_HU.utf8'

# Language specific wording
LRain = " Eső: "
LSnow = " Hó: "

# MQTT Light to turn on/off on main screen (up/down)
Light_MQTT_IDX = 9

ReturnHomeSec      = 60  # Return to Home Screen after x seconds
FrontMotionMinMove = 8   # Detect front motion only if longer than x seconds
DisplayOffTime     = 300 # switch LCD off if no motion for x seconds

# Sensor settings begin
PIN_TMP      = 22          # Connected to DHT22
IDX_TMP      = 10

IDX_LHT      = 11

PIN_MOTION1  = 12          # Connected to HC-SR501
PIN_MOTION2  = 16          # Connected to RCWL-0516

PIN_ADPS     = 17

IDX_MOTION_C = 13         # combined motion

PIN_MOTIONFRONT = 27      # front hc-sr505

IDX_PITMP    = 14

IDX_SIREN     = 15         # output
IDX_RADIO     = 16         # output

PIN_TFT_LED   = 18         # LED PIN of connected TFT, GPIO 18 PWM

IDX_ITAG1_BUTTON = 79
IDX_ITAG1_BUZZER = 80
TAG1_MAC = "" # leave it empty if not used!

# MQTT Topics
mqttSend      = 'domoticz/in'
mqttReceive   = 'domoticz/out'
mqttServer    = "192.168.1.2"
tempdelaysec  = 60          # seconds to loop and send data to mqtt server
DomoticzURL   = "http://192.168.1.2:8080" # API URL to scene timer
DomoticzUsr   = ""                          # Domoticz admin user to scene timer access
DomoticzPw    = ""                          # Domoticz admin pass to scene timer access
AlarmScenePrefix = "AL_"                    # Domoticz scene prefix used to store alarm timers
