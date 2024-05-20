from m5stack import *
from m5stack_ui import *
from uiflow import *

screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0x000000)

# Create labels to display sensor values
datetime_label = M5Label('------- 00.00.0000 - 00:00', x=10, y=0, color=0xffffff, font=FONT_MONT_14)
wifi_status_label = M5Label('....', x=285, y=0, color=0xffffff, font=FONT_MONT_10)
motion_status_label = M5Label('NM', x=255, y=0, color=0xffffff, font=FONT_MONT_10)

temperature_inside_label = M5Label('00.00°C', x=22, y=30, color=0xcd8100, font=FONT_MONT_34)
humidity_inside_label = M5Label('Humidity: 00.00%', x=170, y=30, color=0xffffff, font=FONT_MONT_14)
tvoc_label = M5Label('C02: 0ppm', x=170, y=50, color=0xffffff, font=FONT_MONT_14)

# Display images initially
image1 = M5Img("/flash/res/default_current_weather.png", x=0, y=79)
image2 = M5Img("/flash/res/default_future_weather.png", x=0, y=150)
image3 = M5Img("/flash/res/fetch-bigquery-history-image.png", x=0, y=79)
image3.set_hidden(True)

# Initialize the state of the images
images_visible = True

# Function to toggle image visibility
def toggle_images():
    global images_visible
    if images_visible:
        image1.set_hidden(True)  # Hide the first image
        image2.set_hidden(True)  # Hide the second image
        image3.set_hidden(False)  # Hide the second image
        images_visible = False
    else:
        image1.set_hidden(False)
        image2.set_hidden(False)
        image3.set_hidden(True)
        images_visible = True

# Assign the toggle function to button A
btnA.wasPressed(toggle_images)


