from m5stack import lcd
import network
import time
import usocket as socket


from m5stack_ui import *
from uiflow import *
import time
import unit
import urequests
import wifiCfg
from m5stack import *

# Setup display
lcd.clear()
screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0xd5d5d5)

# WiFi credentials
ssid = 'TP-Link_76C4_5G'
password = '49032826'

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        lcd.println('Connecting to WiFi...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(1)
            lcd.print('.')
    lcd.println('\nWiFi connected')
    lcd.println('IP: ' + wlan.ifconfig()[0])
    return wlan

def get_public_ip():
    try:
        response = socket.getaddrinfo('api.ipify.org', 80)[0][-1]
        s = socket.socket()
        s.connect(response)
        s.send(b'GET /?format=text HTTP/1.1\r\nHost: api.ipify.org\r\n\r\n')
        data = s.recv(1024)
        s.close()

        ip_start = data.find(b'\r\n\r\n') + 4
        ip_end = data.find(b'\r\n', ip_start)
        public_ip = data[ip_start:ip_end].decode()

        return public_ip
    except Exception as e:
        lcd.println('Error getting IP: ' + str(e))
        return None

def main():
    connect_wifi()
    public_ip = get_public_ip()
    if public_ip:
        lcd.println('Public IP: ' + public_ip)
    else:
        lcd.println('Failed to get public IP.')

while True:
    connect_wifi()
    public_ip = get_public_ip()
    ip_label = M5Label('IP: Loading...', x=20, y=40, font=FONT_MONT_22, color=0x000)

    ip_label.set_text('IP: ' + public_ip)







