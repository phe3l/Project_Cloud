from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
import datetime, os

PROJECT_ID = os.getenv('PROJECT_ID')
DATASET_NAME = os.getenv('DATASET_NAME') 
WEATHER_TABLE = os.getenv('WEATHER_TABLE')

class BigQueryClient:
    def __init__(self):
        self.client = bigquery.Client(project=os.getenv('PROJECT_ID'))
        
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
    
    def fetch_weather_data(self):
        try:
            query = f"""SELECT * FROM `{PROJECT_ID}.{DATASET_NAME}.{WEATHER_TABLE}`
                    ORDER BY date DESC, time DESC"""
            
            job_config = bigquery.QueryJobConfig()
                
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            # convert date and time in results to string
            formatted_results = []
            for row in results:
                
                row_dict = {}
                for key, value in row.items():
                    if isinstance(value, datetime.date) or isinstance(value, datetime.time):
                        row_dict[key] = value.isoformat()
                    else:
                        row_dict[key] = value
                
                formatted_results.append(row_dict)
            
            return formatted_results
        
        except Exception as e:
            raise Exception(f"Failed to fetch weather data: {e}")
        
        
    