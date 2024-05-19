from m5stack_ui import M5Screen, M5Label, FONT_MONT_14, FONT_MONT_34, FONT_MONT_10
import unit
from network import WLAN, STA_IF
import urequests
import utime as time
import ntptime
from machine import RTC
import gc
import socket
import struct

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
error_label2 = M5Label('error: ', x=15, y=200, color=0x000, font=FONT_MONT_10)

# WiFi credentials for network connection
wifi_credentials = ('iot-unil', '4u6uch4hpY9pJ2f9')
flask_url = "https://my-test-c7loi7tmea-oa.a.run.app"

# Constants for NTP time synchronization
NTP_DELTA = 3155673600  # 1900-01-01 00:00:00 to 2000-01-01 00:00:00
NTP_QUERY = b'\x1b' + 47 * b'\0'
NTP_SERVER = 'ch.pool.ntp.org'  # NTP server for Switzerland
TIMEZONE_OFFSET = 2 * 3600  # Timezone offset for Central European Time (CET)

# Initialize WLAN
wlan = WLAN(STA_IF)
wlan.active(True)

device_public_ip = None
test_nb = 0

def initialize_wifi_and_time(wifi_credentials):
    """
    Initialize WiFi and synchronize time.
    """
    global wlan, device_public_ip
    if connect_wifi(wifi_credentials):
        if get_device_public_ip() and sync_time_with_ntp():
            wifi_status_label.set_text('Wi-Fi & Time Synced')
        else:
            wifi_status_label.set_text('Wi-Fi Connected, Time Sync Failed')
    else:
        wifi_status_label.set_text('No Wi-Fi')
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
    interval = 1  # Check every second
    start_time = time.time()
    wlan.connect(ssid, password)
    error_label.set_text('Trying to connect to WiFi...{}'.format(ssid))
    while not wlan.isconnected() and (time.time() - start_time < timeout):
        time.sleep(interval)

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
        datetime_label.set_text('{}/{}/{} - {:02}:{:02}'.format(local_time[0], local_time[1], local_time[2], local_time[3], local_time[4]))
    except Exception as e:
        error_label.set_text('Error updating time: {}'.format(e))

def get_current_weather(device_public_ip):
    """
    Fetch the current weather information using the device's public IP address.
    """
    response = None
    try:
        url = "{}/current-weather".format(flask_url)
        response = urequests.post(url, json={"ip": device_public_ip})
        if response.status_code == 200:
            weather_data = response.json()
            outdoor_temp = weather_data['main']['temp']
            outdoor_humidity = weather_data['main']['humidity']
            return outdoor_temp, outdoor_humidity
        else:
            error_label2.set_text('Error getting weather: {}'.format(response.status_code))
            return None
    except Exception as e:
        error_label2.set_text('Error getting weather: {}'.format(e))
        return None
    finally:
        if response:
            response.close()

def send_data(ip, outdoor_temp, outdoor_humidity):
    """
    Send sensor data to the server.
    """
    response = None
    rtc = RTC()
    local_time = rtc.datetime()
    date_str = '{:04d}-{:02d}-{:02d}'.format(local_time[0], local_time[1], local_time[2])
    time_str = '{:02d}:{:02d}:{:02d}'.format(local_time[3], local_time[4], local_time[5])

    data = {
        "values": {
            "indoor_temp": environmental_sensor.temperature,
            "indoor_humidity": environmental_sensor.humidity,
            "ip_address": ip,
            "outdoor_temp": outdoor_temp,
            "outdoor_humidity": outdoor_humidity,
            "indoor_air_quality": gas_detector.eCO2,
            "date": date_str,
            "time": time_str
        }
    }

    try:
        url = "{}/send-to-bigquery".format(flask_url)
        response = urequests.post(url, json=data)
        if response.status_code == 200:
            error_label2.set_text('Data sent successfully')
        else:
            error_label2.set_text('Error sending data: {}'.format(response.status_code))
    except Exception as e:
        error_label2.set_text('Error sending data: {}'.format(e))
    finally:
        if response:
            response.close()

# Initialize WiFi and time synchronization
initialize_wifi_and_time(wifi_credentials)

data_last_sent = time.time() - 60


while True:
    try:
        # Reconnect to WiFi if disconnected
        if not wlan.isconnected():
            wifi_status_label.set_text('Reconnecting WiFi...')
            if connect_wifi(wifi_credentials):
                wifi_status_label.set_text('Wi-Fi Reconnected')
                if sync_time_with_ntp():
                    wifi_status_label.set_text('Wi-Fi & Time Synced')
                else:
                    wifi_status_label.set_text('Wi-Fi Reconnected, Time Sync Failed')
            else:
                wifi_status_label.set_text('Wi-Fi Reconnect Failed')
                continue  # Skip the rest of the loop and retry connection

        now = time.time()

        # Update sensor labels with current values
        env3_temp = environmental_sensor.temperature 
        temperature_inside_label.set_text('{:.2f} °C'.format(env3_temp))

        env3_hum = environmental_sensor.humidity 
        humidity_inside_label.set_text('Humidity: {:.2f} %'.format(env3_hum))

        gas_value = gas_detector.eCO2
        tvoc_label.set_text('C02: {} ppm'.format(gas_value))

        update_datetime_label()

        # Send data to server every 2 minutes
        if now - data_last_sent > 120:
            try:
                current_weather = get_current_weather(device_public_ip)
                if current_weather is not None:
                    test_nb += 1
                    error_label.set_text('Current weather retrieved successfully ({})'.format(test_nb))
                    send_data(device_public_ip, current_weather[0], current_weather[1])
                else:
                    error_label.set_text('Error: Unable to get current weather')
                    continue  # Retry the connection if getting weather fails
                data_last_sent = now
            except Exception as e:
                error_label.set_text('Error getting current weather: {}'.format(e))
                continue  # Retry the connection if there is an exception

    except Exception as e:
        error_label.set_text('Error in main loop: {}'.format(e))

    # Add a delay to avoid flooding the server
    time.sleep(10)