from m5stack import *
from m5stack_ui import *
from uiflow import *
import time
import unit
import urequests

screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0xd5d5d5)

# Initialize the ENV3 unit connected to port A
env3_0 = unit.get(unit.ENV3, unit.PORTA)

# UI Labels for Temperature and Humidity
Temp = M5Label('Temp:', x=19, y=142, color=0x000, font=FONT_MONT_22, parent=None)
Humidity = M5Label('Humidity:', x=19, y=183, color=0x000, font=FONT_MONT_22, parent=None)
temp_value_label = M5Label('T', x=163, y=142, color=0x000, font=FONT_MONT_22, parent=None)
humidity_value_label = M5Label('H', x=158, y=183, color=0x000, font=FONT_MONT_22, parent=None)

# Timing flag for sending data every 5 minutes
temp_flag = 60

while True:
  # Update temperature and humidity display
  temp_value_label.set_text(str(round(env3_0.temperature)) + " °C")
  temp_value_label.set_text_color(0x000000)
  humidity_value_label.set_text(str(round(env3_0.humidity)) + " %")
  humidity_value_label.set_text_color(0x000000)
  
  # Send data every 60 seconds (1 minutes)
  if temp_flag == 60:
    # Data structure to send
    data = {
        "values": {
            "indoor_temp": round(env3_0.temperature),
            "indoor_humidity": round(env3_0.humidity)
        }
    }
    # Send data to your Flask backend
    response = urequests.post("http://192.168.0.100:8080/send-to-bigquery", json=data)
    response.close()  # Always close the response to free up resources
    temp_flag = 0  # Reset the timer flag

  temp_flag += 1
  wait(1)  # Wait for 1 second





