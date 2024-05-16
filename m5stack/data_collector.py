from m5stack_ui import *
from uiflow import *
import network
import socket
import time
import unit
import urequests
from machine import RTC
import utime
import struct  # Assurez-vous d'importer la bibliothèque struct
import random

# Initialize the M5Stack screen
screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0xd5d5d5)

# Configure sensor units connected to ports
environmental_sensor = unit.get(unit.ENV3, unit.PORTA)  # Environmental sensor (temperature, humidity)
gas_detector = unit.get(unit.TVOC, unit.PORTC)  # CO2 gas detector

# Create labels to display sensor values
datetime_label = M5Label('0000/00/00 - 00:00', x=15, y=0, color=0x000000, font=FONT_MONT_14)
wifi_status_label = M5Label('.....', x=160, y=0, color=0x000000, font=FONT_MONT_14)
temperature_inside_label = M5Label('00.00 °C', x=15, y=33, color=0x000, font=FONT_MONT_34)
humidity_inside_label = M5Label('Humidity: 00.00%', x=15, y=86, color=0x000, font=FONT_MONT_14)
tvoc_label = M5Label('Gas TVOC: 0ppb', x=15, y=107, color=0x000, font=FONT_MONT_14)
error_label = M5Label('error: ', x=15, y=180, color=0x000, font=FONT_MONT_10)

# WiFi credentials for network connection
wifi_credentials = [('TP-Link_76C4', '49032826'),('iot-unil', '4u6uch4hpY9pJ2f9'),('TP-Link_76C4_5G', '49032826')]
flask_url = "https://my-test-c7loi7tmea-oa.a.run.app"

# Initialize WLAN outside of the loop
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Initialize device_public_ip
device_public_ip = None

# Constants for NTP time synchronization
NTP_DELTA = 3155673600  # 1900-01-01 00:00:00 to 2000-01-01 00:00:00
NTP_QUERY = b'\x1b' + 47 * b'\0'
NTP_SERVER = 'ch.pool.ntp.org'  # NTP server for Switzerland
TIMEZONE_OFFSET = 2 * 3600  # Timezone offset for Central European Time (CET)

# Function to initialize WiFi and sync time
def initialize_wifi_and_time(wifi_credentials):
    global wlan, device_public_ip
    wlan = connect_wifi(wifi_credentials)
    if wlan and wlan.isconnected():
        if get_device_public_ip() and sync_time_with_ntp():
            wifi_status_label.set_text('Wi-Fi & Time')
        else:
            wifi_status_label.set_text('Wi-Fi Co, Time Sync Failed')
    else:
        wifi_status_label.set_text('No Wi-Fi')
        device_public_ip = None

# Function to connect to WiFi using provided credentials
def connect_wifi(wifi_credentials):
    global wlan
    wlan.active(True)
    if wlan.isconnected():
        return wlan

    timeout = 30  # Augmenter le délai total
    for ssid, password in wifi_credentials:
        start_time = time.time()
        wlan.connect(ssid, password)
        while not wlan.isconnected() and (time.time() - start_time < timeout):
            time.sleep(1)

        if wlan.isconnected():
            return wlan
    wlan.active(False)
    wlan.active(True)
    return None


# Function to get the public IP address of the device
def get_device_public_ip():
    global device_public_ip
    response = None
    try:
        response = urequests.get('http://api.ipify.org/?format=text')
        device_public_ip = response.text
        return True
    except Exception as e:
        error_label.set_text('Error getting IP: {}'.format(e))
        return False
    finally:
        if response:
            response.close()

# Function to set the RTC with the NTP time
def sync_time_with_ntp():
    try:
        # Get the NTP time
        addr = socket.getaddrinfo(NTP_SERVER, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(10)
            s.sendto(NTP_QUERY, addr)
            msg, _ = s.recvfrom(48)
        finally:
            s.close()
        
        ntp_time = struct.unpack('!I', msg[40:44])[0] - NTP_DELTA
        ntp_time += TIMEZONE_OFFSET

        # Set the RTC
        local_time = utime.localtime(ntp_time)
        rtc = RTC()
        rtc.datetime((local_time[0], local_time[1], local_time[2], 0, local_time[3], local_time[4], local_time[5], 0))
        return True
    except Exception as e:
        error_label.set_text('Error setting RTC time: {}'.format(e))
        return False

# Function to update the date_time_label with the current local time from RTC
def update_current_time():
    try:
        local_time = utime.localtime()
        datetime_label.set_text('{}/{}/{} - {:02}:{:02}'.format(local_time[0], local_time[1], local_time[2], local_time[3], local_time[4]))
    except Exception as e:
        error_label.set_text('Error updating time: {}'.format(e))

# Fetches the current weather information using a given IP address.
def get_current_weather(ip):
    response = None
    try:
        url = "{}/current-weather".format(flask_url)
        response = urequests.post(url, json={"ip": ip})
        if response.status_code == 200:
            weather_data = response.json()
            outdoor_temp = weather_data['main']['temp']
            outdoor_humidity = weather_data['main']['humidity']
            icon_code = weather_data['weather'][0]['icon']
            return outdoor_temp, outdoor_humidity, icon_code
        else:
            error_label.set_text('Error getting weather: {}'.format(response.status_code))
            return None
    except Exception as e:
        error_label.set_text('Error getting weather: {}'.format(e))
        return None
    finally:
        if response:
            response.close()

# Function to send data to the server
def send_data(ip, outdoor_temp, outdoor_humidity):
    response = None
    local_time = utime.localtime()
    date = '{:04d}-{:02d}-{:02d}'.format(local_time[0], local_time[1], local_time[2])
    time = '{:02d}:{:02d}:{:02d}'.format(local_time[3], local_time[4], local_time[5])

    data = {
        "values": {
            "indoor_temp": environmental_sensor.temperature,
            "indoor_humidity": environmental_sensor.humidity,
            "ip_address": ip,
            "outdoor_temp": outdoor_temp,
            "outdoor_humidity": outdoor_humidity,
            "indoor_air_quality": gas_detector.eCO2,  
            "date": date,
            "time": time
        }
    }

    try:
        url = "{}/send-to-bigquery".format(flask_url)
        response = urequests.post(url, json=data)
        if response.status_code == 200:
            error_label.set_text('Data sent successfully {}'.format(random.randint(1, 10)))
        else:
            error_label.set_text('Error sending data: {}'.format(response.status_code))
    except Exception as e:
        error_label.set_text('Error sending data: {}'.format(e))
    finally:
        if response:
            response.close()

# Function to update the sensor display values
def update_sensor_display():
    try:
        env3_temp = environmental_sensor.temperature 
        temperature_inside_label.set_text('{:.2f} °C'.format(env3_temp))

        env3_hum = environmental_sensor.humidity 
        humidity_inside_label.set_text('Humidity: {:.2f} %'.format(env3_hum))

        gas_value = gas_detector.eCO2
        tvoc_label.set_text('C02: {} ppm'.format(gas_value))
    except Exception as e:
        error_label.set_text('Error updating display: {}'.format(e))

# Main loop of the device
def main_loop():
    global device_public_ip, wlan
    
    time_last_update = time.time() - 60  # Force immediate time update at start
    data_last_sent = time.time()  

    # Initial setup: connect to WiFi and set RTC time
    initialize_wifi_and_time(wifi_credentials)

    while True:
        now = time.time()
        update_sensor_display()
        try:
            if not wlan.isconnected():
                initialize_wifi_and_time(wifi_credentials)
            
            if wlan.isconnected():
                if device_public_ip is None:
                    if not get_device_public_ip():
                        error_label.set_text('Error: Unable to get public IP')

                if now - time_last_update > 60:
                    update_current_time()
                    time_last_update = now

                if now - data_last_sent > 120:
                    current_weather = get_current_weather(device_public_ip)
                    if current_weather:
                        send_data(device_public_ip, current_weather[0], current_weather[1])
                    else:
                        error_label.set_text('Error: Unable to get current weather')
                    data_last_sent = now
            else:
                wifi_status_label.set_text('No Wi-Fi')
                device_public_ip = None

            time.sleep(5)
        except Exception as e:
            error_label.set_text('Error in main loop: {}'.format(e))
            time.sleep(5)

main_loop()

