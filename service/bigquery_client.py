from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
import datetime

PROJECT_ID = "weather-project-421218"
DATASET_NAME = "weather_dataset" 
WEATHER_TABLE = "weather-records"

class BigQueryClient:
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
    """Insert data into BigQuery."""
    def insert_into_bigquery(self, data: dict):
        try:
            now = datetime.datetime.now()
            data.update({'date': now.strftime('%Y-%m-%d'), 'time': now.strftime('%H:%M:%S')})
            
            columns = ", ".join([f"`{key}`" for key in data.keys()])
            values = ", ".join([f"'{value}'" if isinstance(value, str) else str(value) for value in data.values()])
            
            query = f"INSERT INTO `{PROJECT_ID}.{DATASET_NAME}.{WEATHER_TABLE}` ({columns}) VALUES ({values})"
            self.client.query(query).result()
            return "Data inserted successfully"
        
        except GoogleCloudError as e:
            raise Exception(f"Failed to insert data: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")
    
    