from m5stack_ui import *
from uiflow import *
import network
import socket
import time
import unit
import urequests
from machine import RTC
from libs.image_plus import *
import utime
from m5stack import speaker
import struct
import os

# Initialize the M5Stack screen
screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0xd5d5d5)

# Configure sensor units connected to ports
environmental_sensor = unit.get(unit.ENV3, unit.PORTA)  # Environmental sensor (temperature, humidity)
motion_sensor = unit.get(unit.PIR, unit.PORTB)  # PIR motion sensor
gas_detector = unit.get(unit.TVOC, unit.PORTC)  # TVOC gas detector

# Create labels to display sensor values
datetime_label = M5Label('0000/00/00 - 00:00', x=15, y=0, color=0x000000, font=FONT_MONT_14)
wifi_status_label = M5Label('.....', x=260, y=0, color=0x000000, font=FONT_MONT_14)
temperature_inside_label = M5Label('00.00 °C', x=15, y=33, color=0x000, font=FONT_MONT_34)
humidity_inside_label = M5Label('Humidity: 00.00%', x=15, y=86, color=0x000, font=FONT_MONT_14)
humidity_inside_alert_label = M5Label('', x=150, y=86, color=0xff0000, font=FONT_MONT_14)

tvoc_label = M5Label('Gas TVOC: 0ppb', x=15, y=107, color=0x000, font=FONT_MONT_14)
tvoc_inside_alert_label = M5Label('', x=150, y=107, color=0xff0000, font=FONT_MONT_14)

motion_status_label = M5Label('No', x=275, y=20, color=0x000)

# Outdoor information and forecasts
visual_separator = M5Line(x1=15, y1=135, x2=305, y2=135, color=0x9c9c9c, width=1, parent=None)

outdoor_weather_image = M5Img("res/03d.png", x=165, y=25, parent=None)
outdoor_info_label = M5Label('Updating Outdoor Weather..', x=15, y=148, color=0x000, font=FONT_MONT_14, parent=None)
outdoor_temp_label = M5Label('', x=185, y=148, color=0x000, font=FONT_MONT_14, parent=None)
outdoor_humidity_label = M5Label('', x=254, y=148, color=0x000, font=FONT_MONT_14, parent=None)
    
forecast_image = M5Img("res/03d.png", x=30, y=190)
forecast_title_label = M5Label("Loading tomorrow's forecast...", x=15, y=175, color=0x000, font=FONT_MONT_14, parent=None)
forecast_temp_label = M5Label('', x=225, y=200, color=0x000, font=FONT_MONT_22, parent=None)
forecast_main_label = M5Label('', x=108, y=196, color=0x000, font=FONT_MONT_14, parent=None)
forecast_desc_label = M5Label('', x=108, y=215, color=0x000, font=FONT_MONT_14, parent=None)

# Pending data label
pending_data_label = M5Label('', x=220, y=0, color=0x000000, font=FONT_MONT_14, parent=None)

# WiFi credentials for network connection
wifi_credentials = [('iot-unil', '4u6uch4hpY9pJ2f9'),('TP-Link_76C4', '49032826')]
flask_url = "http://192.168.0.105:8080"

# Constants for NTP time synchronization
NTP_DELTA = 3155673600  # 1900-01-01 00:00:00 to 2000-01-01 00:00:00
NTP_QUERY = b'\x1b' + 47 * b'\0'
NTP_SERVER = 'ch.pool.ntp.org'  # NTP server for Switzerland
TIMEZONE_OFFSET = 2 * 3600  # Timezone offset for Central European Time (CET)

# Variables to store the state of the program
device_public_ip = None
last_motion_state = "No"
last_sound_played_timestamp = 0
sound_playback_interval = 60

# List to accumulate data that will be sent to a server or processed further
outgoing_data_buffer  = []


# Function to connect to WiFi using provided credentials 
start_time_test = time.time() # UNIQUEMENT POUR LES TESTS

def connect_wifi(wifi_credentials):
    # UNIQUEMENT POUR LES TESTS
    #if time.time() - start_time_test < 2 * 60:
    #    return None
     
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan

    timeout = 15  # Total time allowed for attempts

    for ssid, password in wifi_credentials:
        start_time = time.time()
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            if time.time() - start_time > timeout:
                wlan.disconnect()
                break
            time.sleep(1)

        if wlan.isconnected():
            return wlan
    return None

# Function to get the public IP address of the device
def get_device_public_ip():
    global device_public_ip
    try:
        response = urequests.get('http://api.ipify.org/?format=text')
        device_public_ip = response.text
        response.close()
        wifi_status_label.set_text('Wi-Fi')
    except Exception as e:
        wifi_status_label.set_text('No Wi-Fi')
    finally:
        if response:
            response.close()

# Function to get the current NTP time from a given host
def get_ntp_time(host):
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.sendto(NTP_QUERY, addr)
        msg, _ = s.recvfrom(48)
    finally:
        s.close()
    val = struct.unpack('!I', msg[40:44])[0]
    return val - NTP_DELTA

# Function to get the current local time and update the date_time_label with it
def get_current_time():
    ntp_time = get_ntp_time(NTP_SERVER)
    ntp_time += TIMEZONE_OFFSET
    local_time = utime.localtime(ntp_time)
    rtc = RTC()
    rtc.datetime((local_time[0], local_time[1], local_time[2], 0, local_time[3], local_time[4], local_time[5], 0))

    datetime_label.set_text('{}/{}/{} - {}:{}'.format(local_time[0], local_time[1], local_time[2], local_time[3], local_time[4]))


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
            return None
    except Exception as e:
        return None
    finally:
        if response:
            response.close()

# Fetches the future weather information using a given IP address.
def get_future_weather(ip):
    response = None
    try:
        url = "{}/future-weather".format(flask_url)
        response = urequests.post(url, json={"ip": ip})
        if response.status_code == 200:
            weather_data = response.json()
            # The weather forecast for 24 hours ahead is in the 8th position (the API returns forecasts every 3 hours)
            if len(weather_data['list']) >= 8:
                eighth_entry = weather_data['list'][7]
                future_temp = eighth_entry['main']['temp']
                weather_main = eighth_entry['weather'][0]['main']
                weather_description = eighth_entry['weather'][0]['description']
                icon_code = eighth_entry['weather'][0]['icon']
                return future_temp, weather_main, weather_description, icon_code, 
            else:
                return None, None, None, None
        else:
            return None, None, None, None
    except Exception as e:
        return None, None, None, None
    finally:
        if response:
            response.close()

# Function to send data to the server
def send_data(ip, outdoor_temp, outdoor_humidity):
    # Get the current local time
    local_time = utime.localtime()
    date = '{:04d}-{:02d}-{:02d}'.format(local_time[0], local_time[1], local_time[2])
    time = '{:02d}:{:02d}:{:02d}'.format(local_time[3], local_time[4], local_time[5])

    # Prepare the data to be sent
    data = {
        "values": {
            "indoor_temp": environmental_sensor.temperature,
            "indoor_humidity": environmental_sensor.humidity,
            "ip_address": ip,
            "outdoor_temp": outdoor_temp,
            "outdoor_humidity": outdoor_humidity,
            "indoor_air_quality": gas_detector.TVOC,  
            "date": date,
            "time": time
        }
    }

    response = None
    try:
        url = "{}/send-to-bigquery".format(flask_url)
        response = urequests.post(url, json=data)
    except Exception as e:
        print("Failed to send data to BigQuery:", str(e))
    finally:
        if response:
            response.close()

# Function to send pending data to the server
def send_pending_data(ip, environmental_sensor_temperature, environmental_sensor_humidity, gas_detector):
    # Get the current local time
    local_time = utime.localtime()

    # Format the date and time
    date = '{:04d}-{:02d}-{:02d}'.format(local_time[0], local_time[1], local_time[2])
    time = '{:02d}:{:02d}:{:02d}'.format(local_time[3], local_time[4], local_time[5])

    # Prepare the data to be sent
    data = {
        "values": {
            "indoor_temp": environmental_sensor.temperature,
            "indoor_humidity": environmental_sensor.humidity,
            "ip_address": ip,
            "indoor_air_quality": gas_detector,  
            "date": date,
            "time": time
        }
    }

    response = None
    try:
        url = "{}/send-to-bigquery".format(flask_url)
        response = urequests.post(url, json=data)
    except Exception as e:
        print("Failed to send data to BigQuery:", str(e))
    finally:
        if response:
            response.close()

# Function to generate a spoken description of the current weather
def get_weather_spoken(ip):
    url = "{}/generate-current-weather-spoken".format(flask_url)
    response = urequests.post(url, json={"ip": ip})
    if response.status_code == 200:
        with open('/flash/weather.mp3', 'wb') as f:
            f.write(response.content)
        response.close()
        return True
    else:
        return False

# Function to play the spoken weather description
def play_weather_spoken():
    if 'weather.mp3' in os.listdir('/flash'):
        speaker.playWAV("/flash/weather.mp3", volume=6)

# Function to update the sound playback based on the motion sensor state
def update_sound():
    global last_motion_state, last_sound_played_timestamp, sound_playback_interval, device_public_ip
    current_motion_state = "Yes" if motion_sensor.state == 1 else "No"
    motion_status_label.set_text('{}'.format(current_motion_state))

    current_time = time.time()
    if current_motion_state == "Yes" and last_motion_state == "No":
        if current_time - last_sound_played_timestamp >= sound_playback_interval:
            if get_weather_spoken(device_public_ip):
                play_weather_spoken()
            last_sound_played_timestamp = current_time
    last_motion_state = current_motion_state



def check_and_alert(env3_hum, gas_value):

    if env3_hum < 30.00:
        humidity_inside_alert_label.set_text('Humidity Too LOW')
    elif env3_hum > 60.00:
        humidity_inside_alert_label.set_text('Humidity Too HIGH')
    else:
        humidity_inside_alert_label.set_text('')

    if gas_value > 100: 
        tvoc_inside_alert_label.set_text('Poor Air Quality')
    else:
        tvoc_inside_alert_label.set_text('')

# Function to update the sensor display values
def update_sensor_display():
    env3_temp = environmental_sensor.temperature 
    temperature_inside_label.set_text('{:.2f} °C'.format(env3_temp))

    env3_hum = environmental_sensor.humidity 
    humidity_inside_label.set_text('Humidity: {:.2f} %'.format(env3_hum))

    gas_value = gas_detector.TVOC
    tvoc_label.set_text('Gas TVOC: {} ppb'.format(gas_value))

    check_and_alert(env3_hum, gas_value)
    

# Function to update the API display values
def update_api_display(current_weather, futur_weather):
    global outdoor_weather_image, forecast_image

    outdoor_temp_label.set_text('{:.2f} °C'.format(current_weather[0]))
    outdoor_humidity_label.set_text('{:.2f} %'.format(current_weather[1]))

    del outdoor_weather_image
    outdoor_weather_image = M5Img('res/{}.png'.format(current_weather[2]), x=165, y=25, parent=None)

    forecast_title_label.set_text("Tomorrow's forecast:")
    del forecast_image
    forecast_image = M5Img('res/{}.png'.format(futur_weather[3]), x=30, y=190)
    forecast_temp_label.set_text('{:.2f} °C'.format(futur_weather[0]))
    forecast_main_label.set_text('{}'.format(futur_weather[1]))
    forecast_desc_label.set_text('{}'.format(futur_weather[2]))

# Main loop of the devic
def main_loop():
    global device_public_ip, outgoing_data_buffer 
    
    # Initial forced updates
    api_last_update = time.time() - 600  # Force immediate update at start
    time_last_update = time.time() - 60  # Force immediate time update at start
    data_last_sent = time.time()  

    while True:
        now = time.time()
        update_sensor_display()
        
        wlan = connect_wifi(wifi_credentials)
        if wlan:
            if device_public_ip is None:
                get_device_public_ip()

            # If connection is restored, send all stored data
            for data in outgoing_data_buffer :
                send_pending_data(device_public_ip, data[0], data[1], data[2])
            # Clear the buffer after sending data
            outgoing_data_buffer = []
            pending_data_label.set_text('{}'.format(len(outgoing_data_buffer) if len(outgoing_data_buffer) > 0 else ""))
            
            update_sound()

            # Update the current time every 60 seconds
            if now - time_last_update > 60:
                get_current_time()
                time_last_update = now

            # Update weather data every 10 minutes (600 seconds)
            if now - api_last_update > 600:
                current_weather = get_current_weather(device_public_ip)
                futur_weather = get_future_weather(device_public_ip)
                if current_weather and futur_weather:
                    outdoor_info_label.set_text('Outdoor Weather:')
                    update_api_display(current_weather, futur_weather)
                    api_last_update = now

            # Send data every 2 minutes (120 seconds)
            if now - data_last_sent > 120:
                send_data(device_public_ip, current_weather[0], current_weather[1])
                data_last_sent = now
        else:
            wifi_status_label.set_text('No Wi-Fi')
            device_public_ip = None

            # Append sensor data to buffer if not sent after 120 seconds         
            if now - data_last_sent > 120:
                outgoing_data_buffer.append((environmental_sensor.temperature, environmental_sensor.humidity, gas_detector.TVOC))
                data_last_sent = now
            
            pending_data_label.set_text('{}'.format(len(outgoing_data_buffer )))

        # Calculate the time to sleep, ensure it's not negative
        next_action = min(time_last_update + 60, api_last_update + 300, data_last_sent + 120)
        sleep_time = max(5, next_action - now)
        #time.sleep(sleep_time)
        time.sleep(1)


main_loop()
