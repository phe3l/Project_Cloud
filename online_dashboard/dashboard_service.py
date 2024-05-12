import requests
import os
import pandas as pd

SERVICE_URL = os.getenv("SERVICE_CLOUD_RUN_URL")

class DashboardService:
    def __init__(self) -> None:
        self.base_url = SERVICE_URL
        
    def fetch_weather_data(self):
        try:
            url = f"{self.base_url}/fetch-bigquery-history"
            response = requests.post(url)
            
           
            results = pd.DataFrame(response.json())
            
            results = results[results['date'].notnull() & results['time'].notnull()]
            
            results['datetime'] = pd.to_datetime(results['date'] + " " + results['time'])
            results = results.drop(columns=['date', 'time'])
            
            return results
        
        except Exception as e:
            raise Exception(f"Failed to fetch weather history: {e}")