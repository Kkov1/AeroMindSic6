import network
import time

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.scan()
wlan.connect("Hayolo Kaget", "gajiguruhonorer")
wlan.isconnected()

time.sleep(3)
