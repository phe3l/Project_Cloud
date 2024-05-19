from m5stack_ui import M5Screen, M5Label, FONT_MONT_14, FONT_MONT_34,FONT_MONT_10
import unit
from network import WLAN, STA_IF
import urequests
import utime as time
import ntptime
from machine import RTC
import gc
import socket
import struct
from m5stack import lcd, rgb, speaker
import os

# Initialize the M5Stack screen
screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0x000000)
rgb.setBrightness(10)

# Configure sensor units connected to ports
environmental_sensor = unit.get(unit.ENV3, unit.PORTA)  # Environmental sensor (temperature, humidity)
motion_sensor = unit.get(unit.PIR, unit.PORTB)  # PIR motion sensor
gas_detector = unit.get(unit.TVOC, unit.PORTC)  # CO2 gas detector

# Create labels to display sensor values
datetime_label = M5Label('------- 00.00.0000 - 00:00', x=10, y=0, color=0xffffff, font=FONT_MONT_14)
wifi_status_label = M5Label('....', x=285, y=0, color=0xffffff, font=FONT_MONT_10)
motion_status_label = M5Label('NM', x=255, y=0, color=0xffffff, font=FONT_MONT_10)

temperature_inside_label = M5Label('00.00°C', x=22, y=30, color=0xcd8100, font=FONT_MONT_34)
humidity_inside_label = M5Label('Humidity: 00.00%', x=170, y=30, color=0xffffff, font=FONT_MONT_14)
tvoc_label = M5Label('C02: 0ppm', x=170, y=50, color=0xffffff, font=FONT_MONT_14)
#lcd.image(0, 79, '/flash/res/default_current_weather.png')
#lcd.image(0, 150, '/flash/res/default_future_weather.png')

# Error label & pending data label
pending_data_label = M5Label('', x=240, y=0, color=0xffffff, font=FONT_MONT_10)
error_label = M5Label('', x=10, y=16, color=0xffffff, font=FONT_MONT_10)

# WiFi credentials for network connection
wifi_credentials = ('iot-unil', '4u6uch4hpY9pJ2f9')
flask_url = "http://130.223.233.210:8080"

# Initialize WLAN
wlan = WLAN(STA_IF)
wlan.active(True)

# Variables to store the state of the program
device_public_ip = None
last_motion_state = "NM"
last_sound_played_timestamp = 0
sound_playback_interval = 60

# List to accumulate data that will be sent to a server or processed further
outgoing_data_buffer  = []

# Constants for NTP time synchronization
NTP_DELTA = 3155673600  # 1900-01-01 00:00:00 to 2000-01-01 00:00:00
NTP_QUERY = b'\x1b' + 47 * b'\0'
NTP_SERVER = 'ch.pool.ntp.org'  # NTP server for Switzerland
TIMEZONE_OFFSET = 2 * 3600  # Timezone offset for Central European Time (CET)

def initialize_wifi_and_time(wifi_credentials):
    """
    Initialize WiFi and synchronize time.
    """
    global wlan, device_public_ip
    if connect_wifi(wifi_credentials):
        if get_device_public_ip() and sync_time_with_ntp():
            wifi_status_label.set_text('W+T')
        else:
            wifi_status_label.set_text('W-T')
    else:
        wifi_status_label.set_text('-W')
        device_public_ip = None

def connect_wifi(wifi_credentials):
    """
    Connect to the WiFi using provided credentials.
    """
    global wlan
    wlan.active(True)
    if wlan.isconnected():
        return True

    ssid, password = wifi_credentials
    timeout = 30  # Timeout in seconds
    start_time = time.time()
    wlan.connect(ssid, password)
    error_label.set_text('Trying to connect to WiFi...{}'.format(ssid))
    while not wlan.isconnected() and (time.time() - start_time < timeout):
        time.sleep(1)

    if wlan.isconnected():
        error_label.set_text('Network config: {}'.format(wlan.ifconfig()))
    else:
        error_label.set_text('Failed to connect to WiFi')
    return wlan.isconnected()

def get_device_public_ip():
    """
    Get the public IP address of the device.
    """
    global device_public_ip
    response = None
    retries = 3
    while retries > 0:
        try:
            response = urequests.get('http://api.ipify.org/?format=text')
            device_public_ip = response.text
            return True
        except Exception as e:
            error_label.set_text('Error getting IP: {}'.format(e))
            retries -= 1
            time.sleep(5)  # Wait before retrying
        finally:
            if response:
                response.close()
    return False

def sync_time_with_ntp(retries=3):
    """
    Synchronize the time with an NTP server.
    """
    while retries > 0:
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
            local_time = time.localtime(ntp_time)
            rtc = RTC()
            rtc.datetime((local_time[0], local_time[1], local_time[2], 0, local_time[3], local_time[4], local_time[5], 0))
            return True
        except Exception as e:
            error_label.set_text('Error setting RTC time: {}'.format(e))
            retries -= 1
            time.sleep(5)  # Wait before retrying
    return False

def update_datetime_label():
    """
    Update the datetime label with the current time.
    """
    try:
        local_time = time.localtime()
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_of_week = days_of_week[local_time[6]]  # local_time[6] is the weekday (0=Monday, 6=Sunday)
        
        formatted_date = '{} {:02d}.{:02d}.{:04d} - {:02d}:{:02d}'.format(
            day_of_week, local_time[2], local_time[1], local_time[0], local_time[3], local_time[4]
        )
        
        datetime_label.set_text(formatted_date)
    except Exception as e:
        error_label.set_text('Error updating time: {}'.format(e))


def get_current_weather(ip):
    """
    Fetch the image of the current weather information using the device's public IP address.
    """
    response = None
    try:
        url = "{}/generate-weather-image".format(flask_url)
        response = urequests.post(url, json={"ip": ip})
        if response.status_code == 200:
            # Sauvegarder l'image dans un fichier temporaire
            image_path = '/flash/weather_image.png'
            with open(image_path, 'wb') as f:
                f.write(response.content)

            # Afficher l'image sur l'écran M5Stack
            #lcd.clear(lcd.WHITE)  # Effacer l'écran
            lcd.image(0, 79, image_path)  # Afficher l'image
            return True
        else:
            error_label.set_text('url : {}'.format(url))
            error_label.set_text('Error getting weather: {}'.format(response.status_code))
            return False
    except Exception as e:
        error_label.set_text('Error getting weather: {}'.format(e))
        return False
    finally:
        if response:
            response.close()

def get_future_weather(ip):
    """
    Fetch the image of the current weather information using the device's public IP address.
    """
    response = None
    try:
        url = "{}/generate-future-weather-image".format(flask_url)
        response = urequests.post(url, json={"ip": ip})
        if response.status_code == 200:
            # Sauvegarder l'image dans un fichier temporaire
            image_path = '/flash/future_weather_image.png'
            with open(image_path, 'wb') as f:
                f.write(response.content)

            # Afficher l'image sur l'écran M5Stack
            #lcd.clear(lcd.WHITE)  # Effacer l'écran
            lcd.image(0, 150, image_path)  # Afficher l'image
            return True
        else:
            error_label.set_text('url : {}'.format(url))
            error_label.set_text('Error getting weather: {}'.format(response.status_code))
            return False
    except Exception as e:
        error_label.set_text('Error getting weather: {}'.format(e))
        return False
    finally:
        if response:
            response.close()

def send_data(ip):
    """
    Send sensor data to the server.
    """
    response = None
    local_time = time.localtime()
    date_str = '{:04d}-{:02d}-{:02d}'.format(local_time[0], local_time[1], local_time[2])
    time_str = '{:02d}:{:02d}:{:02d}'.format(local_time[3], local_time[4], local_time[5])

    data = {
        "values": {
            "ip_address": ip,
            "date": date_str,
            "time": time_str,
            "indoor_temp": environmental_sensor.temperature,
            "indoor_humidity": environmental_sensor.humidity,
            "indoor_air_quality": gas_detector.eCO2
        }
    }

    try:
        url = "{}/send-to-bigquery".format(flask_url)
        response = urequests.post(url, json=data)
        if response.status_code == 200:
            error_label.set_text('Data sent successfully {}'.format({time_str}))
        else:
            error_label.set_text('Error sending data: {}'.format(response.status_code))
    except Exception as e:
        error_label.set_text('Error sending data: {}'.format(e))
    finally:
        if response:
            response.close()

def send_pending_data(ip, pending_data_buffer, reconnection_time):
    """
    Send pending sensor data to the server.
    """
    interval_between_data = 120  # Interval between data additions in seconds
    num_data_points = len(pending_data_buffer)

    for i, data_point in enumerate(pending_data_buffer):
        # Calculate the timestamp for the data point
        data_time = reconnection_time - ((num_data_points - 1 - i) * interval_between_data)
        local_time = time.localtime(data_time)
        date_str = '{:04d}-{:02d}-{:02d}'.format(local_time[0], local_time[1], local_time[2])
        time_str = '{:02d}:{:02d}:{:02d}'.format(local_time[3], local_time[4], local_time[5])

        data = {
            "values": {
                "ip_address": ip,
                "date": date_str,
                "time": time_str,
                "indoor_temp": data_point[0],
                "indoor_humidity": data_point[1],
                "indoor_air_quality": data_point[2]
            }
        }

        try:
            url = "{}/send-pending-to-bigquery".format(flask_url)
            response = urequests.post(url, json=data)
            if response.status_code == 200:
                error_label.set_text('Pending data sent successfully')
            else:
                error_label.set_text('Error sending pending data: {}'.format(response.status_code))
        except Exception as e:
            error_label.set_text('Error sending pending data: {}'.format(e))
        finally:
            if response:
                response.close()

# Callback function to handle WiFi reconnection data sending
def on_wifi_reconnected():
    global outgoing_data_buffer
    if outgoing_data_buffer:
        send_pending_data(device_public_ip, outgoing_data_buffer, time.time())
        outgoing_data_buffer.clear()

def get_weather_spoken(ip):
    """
    Generate a spoken description of the current weather.
    """
    url = "{}/generate-current-weather-spoken".format(flask_url)
    response = None
    try:
        response = urequests.post(url, json={"ip": ip})
        if response.status_code == 200:
            with open('/flash/weather.mp3', 'wb') as f:
                f.write(response.content)
            return True
        else:
            error_label.set_text('Error generating spoken weather: {}'.format(response.status_code))
            return False
    except Exception as e:
        error_label.set_text('Error in get_weather_spoken: {}'.format(e))
        return False
    finally:
        if response:
            response.close()


def play_weather_spoken():
    """
    Play the spoken weather description if the file exists.
    """
    try:
        if 'weather.mp3' in os.listdir('/flash'):
            speaker.playWAV("/flash/weather.mp3", volume=6)
        else:
            error_label.set_text('weather.mp3 not found')
    except Exception as e:
        error_label.set_text('Error in play_weather_spoken: {}'.format(e))

# Function to update the sound playback based on the motion sensor state
def update_sound():
    global last_motion_state, last_sound_played_timestamp, sound_playback_interval, device_public_ip
    current_motion_state = "M" if motion_sensor.state == 1 else "NM"
    motion_status_label.set_text('{}'.format(current_motion_state))

    current_time = time.time()
    if current_motion_state == "M" and last_motion_state == "NM":
        if current_time - last_sound_played_timestamp >= sound_playback_interval:
            if get_weather_spoken(device_public_ip):
                play_weather_spoken()
            last_sound_played_timestamp = current_time
    last_motion_state = current_motion_state

def check_and_alert(env3_hum, gas_value):
    alert_triggered = False

    # Check humidity
    if env3_hum > 60.00:
        humidity_inside_label.set_text_color(0xFF0000)
        alert_triggered = True
    elif env3_hum < 40.00:
        humidity_inside_label.set_text_color(0x0000FF)
        alert_triggered = True
    else:
        humidity_inside_label.set_text_color(0xffffff)  

    # Check gas value
    if gas_value > 1000:
        tvoc_label.set_text_color(0xFF0000)
        alert_triggered = True
    else:
        tvoc_label.set_text_color(0xffffff)  
    
    # Trigger LED blink if alert is triggered
    if alert_triggered:
        blink_red_led(duration=9, interval=0.5) 

    return alert_triggered

def blink_red_led(duration, interval):
    """
    Blink the red LED for a specified duration and interval.
    """
    end_time = time.time() + duration
    while time.time() < end_time:
        rgb.setColorAll(0xFF0000)  # Turn LED red
        time.sleep(interval)
        rgb.setColorAll(0x000000)  # Turn LED off
        time.sleep(interval)

# Function to update the sensor display values
def update_sensor_display():
    env3_temp = environmental_sensor.temperature 
    temperature_inside_label.set_text('{:.2f}°C'.format(env3_temp))

    env3_hum = environmental_sensor.humidity 
    humidity_inside_label.set_text('Humidity: {:.2f} %'.format(env3_hum))

    gas_value = gas_detector.eCO2
    tvoc_label.set_text('C02: {} ppm'.format(gas_value))

    check_and_alert(env3_hum, gas_value)

# Initialize WiFi and time synchronization
initialize_wifi_and_time(wifi_credentials)

# Main loop of the device
def main_loop():
    global device_public_ip, outgoing_data_buffer 
    
    # Initial forced updates
    time_last_update = time.time() - 60  # Force immediate time update at start
    data_last_sent = time.time() - 120  # Force data send 3 minutes after start
    weather_last_checked = time.time() - 120  # Force immediate weather check at start
    future_last_checked = time.time() - 3600  # Force immediate weather check at start

    while True:
        try:
            update_sensor_display()
            if wlan.isconnected():
                if outgoing_data_buffer:
                    on_wifi_reconnected()
            
                update_datetime_label()
                update_sound()

                now = time.time()

                # Check if it's time to fetch the current weather image
                if now - weather_last_checked >= 120 and wlan.isconnected():
                    if get_current_weather(device_public_ip):
                        weather_last_checked = now
                    else:
                        weather_last_checked = now

                # Check if it's time to fetch the current weather image
                if now - future_last_checked >= 3600 and wlan.isconnected():
                    if get_future_weather(device_public_ip):
                        future_last_checked = now
                    else:
                        future_last_checked = now

                # Check if it's time to send data
                if now - data_last_sent >= 300:  # 300 seconds = 5 minutes
                    if wlan.isconnected():
                        send_data(device_public_ip)  # You should replace 0, 0 with the actual outdoor temp and humidity if available
                        data_last_sent = now

            else:
                # Reconnect to WiFi if disconnected
                initialize_wifi_and_time(wifi_credentials)

                # Append sensor data to buffer if not sent after 120 seconds         
                if now - data_last_sent > 120:
                    outgoing_data_buffer.append((environmental_sensor.temperature, environmental_sensor.humidity, gas_detector.TVOC))
                    data_last_sent = now
                
                pending_data_label.set_text('{}'.format(len(outgoing_data_buffer )))

        except Exception as e:
            error_label.set_text('Error in main loop: {}'.format(e))

        # Add a delay to avoid flooding the server
        time.sleep(7)

main_loop()