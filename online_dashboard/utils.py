import pandas as pd
import requests


columns_rename_map = {"indoor_temp": "Indoor Temperature", "outdoor_temp": "Outdoor Temperature", "indoor_humidity" : "Indoor Humidity", "outdoor_humidity" : "Outdoor Humidity", "indoor_air_quality": "Indoor Air Quality"}

def prepare_daily_data(df: pd.DataFrame):

    dff = df.copy()
    dff.set_index("datetime", inplace=True)
    dff.drop(columns=["ip_address"], inplace=True)
    dff.rename(columns=columns_rename_map, inplace=True)
    
    return dff


def calculate_daily_averages(df: pd.DataFrame):
    dff = df.copy()
    dff.set_index("datetime", inplace=True)
    dff.rename(columns=columns_rename_map, inplace=True)
    dff.drop(columns=["ip_address"], inplace=True)
    
    daily_averages = dff.resample("D").mean()
    
    return daily_averages


def get_location_via_ip(ip):
    try:
        API_URL = "http://ip-api.com/json/" + ip
        params = {"fields": "city,country"}
        
        response = requests.get(API_URL, params=params)
        
        return response.json()["city"] + ", " + response.json()["country"]
    except Exception as e:
        raise Exception(f"Failed to fetch location using ip: {e}")
    
    
def get_weather_icon_by_description(description):
    
    if description == "Clear":
        return "ph:sun-fill"
    elif description == "Clouds":
        return "bi:clouds-fill"
    elif description == "Rain":
        return "f7:cloud-rain-fill"
    elif description == "Snow":
        return "bi:cloud-snow-fill"
    elif description == "Thunderstorm":
        return "ion:thunderstorm-sharp"
    elif description == "Drizzle":
        return "f7:cloud-drizzle-fill"
    else:
        return "material-symbols:cloud"
    
    
    
    
    
