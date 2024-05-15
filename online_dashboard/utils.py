from datetime import datetime, timedelta
import pandas as pd
from dashboard_service import DashboardService
import requests

# def generate_time_series(selected_date) -> pd.date_range:
#     start_time = datetime.combine(selected_date, datetime.min.time())
#     end_time = datetime.combine(selected_date, datetime.max.time())
#     return pd.date_range(start_time, end_time, freq="1h")

columns_rename_map = {"indoor_temp": "Indoor Temperature", "outdoor_temp": "Outdoor Temperature", "indoor_humidity" : "Indoor Humidity", "outdoor_humidity" : "Outdoor Humidity", "indoor_air_quality": "Indoor Air Quality"}

def prepare_daily_data(df: pd.DataFrame, selected_date):
    start_time = datetime.combine(selected_date, datetime.min.time())
    end_time = datetime.combine(selected_date, datetime.max.time())
    
    #add row in df 
    new_rows = pd.DataFrame({
        "datetime": [start_time, end_time],
        "indoor_air_quality": [None, None],
        "indoor_humidity": [None, None],
        "indoor_temp": [None, None],
        "ip_address": [None, None],
        "outdoor_humidity": [None, None],
        "outdoor_temp": [None, None],
        "outdoor_weather": [None, None]
    })
    
    combined_df = pd.concat([df, new_rows], ignore_index=True)
    
    return combined_df


def calculate_daily_averages(df: pd.DataFrame):
    dff = df.copy()
    dff.set_index("datetime", inplace=True)
    dff.rename(columns=columns_rename_map, inplace=True)
    dff.drop(columns=["ip_address", "outdoor_weather"], inplace=True)
    
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
    

    
    
    
