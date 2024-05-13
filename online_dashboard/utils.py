from datetime import datetime, timedelta
import pandas as pd

# def generate_time_series(selected_date) -> pd.date_range:
#     start_time = datetime.combine(selected_date, datetime.min.time())
#     end_time = datetime.combine(selected_date, datetime.max.time())
#     return pd.date_range(start_time, end_time, freq="1h")

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
    daily_avg = df.resample("D", on="datetime").mean()
    daily_avg["datetime"] = daily_avg.index
    return daily_avg
    