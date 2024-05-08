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
import utime

screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0xd5d5d5)

# Initialize the ENV3 unit connected to port A
env3_0 = unit.get(unit.ENV3, unit.PORTA)
# Initialize the PIR Motion sensor connected to port B
pir_sensor = unit.get(unit.PIR, unit.PORTB)
# Initialize the Gas unit connected to port C
gas_unit = unit.get(unit.TVOC, unit.PORTC)

# Create labels to display sensor values
datetime_label = M5Label('0000/00/00 - 00:00', x=15, y=0, color=0x000000, font=FONT_MONT_14, parent=None)
wifi_label = M5Label('.....', x=262, y=0, color=0x000000, font=FONT_MONT_14, parent=None)
env3_temp_label = M5Label('00.00 °C', x=15, y=33, color=0x000, font=FONT_MONT_34, parent=None)
image0 = M5Img("res/base.png", x=155, y=0, parent=None)
env3_hum_label = M5Label('Humidity: 00.00%', x=15, y=86, color=0x000, font=FONT_MONT_14, parent=None)
gas_label = M5Label('Gas TVOC: 0ppb', x=15, y=107, color=0x000, font=FONT_MONT_14, parent=None)

line0 = M5Line(x1=15, y1=135, x2=305, y2=135, color=0x000, width=1, parent=None)
label4 = M5Label('Outdoor Information: Update...', x=15, y=148, color=0x000, font=FONT_MONT_14, parent=None)
outdoor_temp_label = M5Label('', x=185, y=148, color=0x000, font=FONT_MONT_14, parent=None)
outdoor_hum_label = M5Label('', x=254, y=148, color=0x000, font=FONT_MONT_14, parent=None)
    
label7 = M5Label("Tomorrow's forecast: Update...", x=15, y=175, color=0x000, font=FONT_MONT_14, parent=None)

label8 = M5Label('', x=225, y=200, color=0x000, font=FONT_MONT_22, parent=None)
label9 = M5Label('', x=108, y=196, color=0x000, font=FONT_MONT_14, parent=None)
label10 = M5Label('', x=108, y=218, color=0x000, font=FONT_MONT_14, parent=None)



# WiFi credentials for connecting to the network
wifi_credentials = [('TP-Link_76C4', '49032826'),('iot-unil', '4u6uch4hpY9pJ2f9')]
flask_url = "http://192.168.0.103:8080"

# Constants
NTP_DELTA = 3155673600  # 1900-01-01 00:00:00 to 2000-01-01 00:00:00
NTP_QUERY = b'\x1b' + 47 * b'\0'
NTP_SERVER = 'ch.pool.ntp.org'  # NTP server for Switzerland
TIMEZONE_OFFSET = 2 * 3600  # Timezone offset (2 hours standard, 3 hours daylight saving time)
public_ip = None

# Function to connect to WiFi using provided credentials
def connect_wifi(wifi_credentials):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan

    timeout = 15  # Total time allowed for attempts
    start_time = time.time()

    for ssid, password in wifi_credentials:
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            if time.time() - start_time > timeout:
                wlan.disconnect()
                return None
            time.sleep(1)

    if wlan.isconnected():
        return wlan
    else:
        return None

# Function to get the public IP address of the device
def get_public_ip():
    global public_ip
    try:
        response = urequests.get('http://api.ipify.org/?format=text')
        public_ip = response.text
        response.close()
        wifi_label.set_text('Wi-Fi')
    except Exception as e:
        wifi_label.set_text('No Wi-Fi')
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
    # Update the label text with the time and date
    datetime_label.set_text('{}/{}/{} - {}:{}'.format(local_time[0], local_time[1], local_time[2], local_time[3], local_time[4]))
    
    # Convert the local time tuple back to UNIX timestamp and return it
    #unix_timestamp = utime.mktime(local_time)
    # return unix_timestamp

def get_current_weather(ip):
    response = None  # Initialiser response ici pour garantir qu'elle est définie avant le bloc try
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

def get_future_weather(ip):
    response = None
    try:
        url = "{}/future-weather".format(flask_url)  # Assurez-vous que flask_url est défini quelque part dans votre code
        response = urequests.post(url, json={"ip": ip})
        if response.status_code == 200:
            weather_data = response.json()
            # Obtenir directement le 8ème objet de la liste des prévisions
            if len(weather_data['list']) >= 8:  # Vérifiez si la liste contient au moins 8 objets
                eighth_entry = weather_data['list'][7]  # L'indexation commence à 0, donc 7 représente le 8ème objet
                future_temp = eighth_entry['main']['temp']
                icon_code = eighth_entry['weather'][0]['icon']
                weather_main = eighth_entry['weather'][0]['main']
                weather_description = eighth_entry['weather'][0]['description']
                return future_temp, icon_code, weather_main, weather_description  # Retourner les informations demandées
            else:
                return None, None, None, None  # Si la liste contient moins de 8 éléments
        else:
            return None, None, None, None
    except Exception as e:
        print("Error while fetching future weather:", str(e))
        return None, None, None, None
    finally:
        if response:
            response.close()  # Assurez-vous de fermer la réponse après traitement

def send_data(ip, outdoor_temp, outdoor_humidity):
    # Get the current local time
    local_time = utime.localtime()

    # Format the date and time
    date = '{:04d}-{:02d}-{:02d}'.format(local_time[0], local_time[1], local_time[2])
    time = '{:02d}:{:02d}:{:02d}'.format(local_time[3], local_time[4], local_time[5])

    # Prepare the data to be sent
    data = {
        "values": {
            "indoor_temp": env3_0.temperature,
            "indoor_humidity": env3_0.humidity,
            "ip_address": ip,
            "outdoor_temp": outdoor_temp,
            "outdoor_humidity": outdoor_humidity,
            "indoor_air_quality": gas_unit.TVOC,  
            "date": date,
            "time": time
        }
    }

    response = None
    try:
        # Send the data to BigQuery
        url = "{}/send-to-bigquery".format(flask_url)
        response = urequests.post(url, json=data)
    except Exception as e:
        # Print any errors that occur
        print("Failed to send data to BigQuery:", str(e))
    finally:
        # Close the response if it was opened
        if response:
            response.close()


def update_sensor_display():
    env3_temp = env3_0.temperature 
    env3_hum = env3_0.humidity 
    gas_value = gas_unit.TVOC
    env3_temp_label.set_text('{:.2f} °C'.format(env3_temp))
    env3_hum_label.set_text('Humidity: {:.2f} %'.format(env3_hum))
    gas_label.set_text('Gas TVOC: {} ppb'.format(gas_value))

def update_api_display(current_weather, futur_weather):
    outdoor_temp_label.set_text('{:.2f} °C'.format(current_weather[0]))
    outdoor_hum_label.set_text('{:.2f} %'.format(current_weather[1]))
    image0 = M5Img('res/{}.png'.format(current_weather[2]), x=155, y=0)

    label7.set_text("Tomorrow's forecast:")
    image1 = M5Img('res/{}.png'.format(futur_weather[1]), x=0, y=190)
    label8.set_text('{:.2f} °C'.format(futur_weather[0]))
    label9.set_text('{}'.format(futur_weather[2]))
    label10.set_text('{}'.format(futur_weather[3]))

    #TEST
    #image_url = 'https://openweathermap.org/img/wn/{}.png'.format(current_weather[2])
    #label80 = M5Label('{}:{}'.format(image_url), x=0, y=125, color=0x000, font=FONT_MONT_10, parent=None)


# Fonction pour démarrer la boucle principale
def main_loop():
    global public_ip
    
    api_last_update = time.time() - 300  # Force immediate update at start
    time_last_update = time.time() - 60  # Force immediate time update at start
    data_last_sent = time.time() - 120  # Initialiser pour forcer l'envoi immédiat des données

    while True:
        now = time.time()
        update_sensor_display()
        
        wlan = connect_wifi(wifi_credentials)
        if wlan:
            if public_ip is None:
                get_public_ip()
            
            if now - time_last_update > 60:
                get_current_time()
                time_last_update = now

            if now - api_last_update > 300:
                current_weather = get_current_weather(public_ip)
                futur_weather = get_future_weather(public_ip)
                if current_weather and futur_weather:
                    label4.set_text('Outdoor Information:')
                    update_api_display(current_weather, futur_weather)
                    api_last_update = now

            if now - data_last_sent > 120:
                send_data(public_ip, current_weather[0], current_weather[1] if current_weather else None)
                data_last_sent = now
        else:
            wifi_label.set_text('No Wi-Fi')
            public_ip = None

        # Calculez le temps nécessaire pour dormir, assurez-vous qu'il ne soit pas négatif
        next_action = min(time_last_update + 60, api_last_update + 300, data_last_sent + 120)
        sleep_time = max(0, next_action - now)
        time.sleep(sleep_time)

main_loop()
