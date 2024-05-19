import unittest
import requests
import os

class ServiceTestCloudRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = os.getenv('SERVICE_CLOUD_RUN_URL')

    def test_insert_weather(self):
        # Test sending data to BigQuery via Cloud Run
        url = f'{self.base_url}/send-to-bigquery'
        payload = {
            "values": {
                "date": "2024-05-01", "time": "17:29:54", "indoor_temp": 28.0, 
                "indoor_humidity": 39.0, "outdoor_temp": 21.9, "outdoor_humidity": 28.0,
                "ip_address": "86.111.136.24"
            }
        }
        response = requests.post(url, json=payload)
        self.assertEqual(response.status_code, 200)

    def test_get_current_weather_missing_ip(self):
        url = f'{self.base_url}/current-weather'
        response = requests.post(url, json={})
        self.assertEqual(response.status_code, 400)

    def test_get_current_weather(self):
        url = f'{self.base_url}/current-weather'
        response = requests.post(url, json={"ip": "130.223.251.132"})
        self.assertEqual(response.status_code, 200)

    def test_get_future_weather(self):
        # Test getting future weather
        url = f'{self.base_url}/future-weather'
        response = requests.post(url, json={"ip": "130.223.251.132"})
        self.assertEqual(response.status_code, 200)
        
    def test_generate_current_weather_spoken_missing_ip(self):
        # Test generating spoken weather description without IP address
        url = f'{self.base_url}/generate-current-weather-spoken'
        response = requests.post(url, json={})
        self.assertEqual(response.status_code, 400)

    def test_generate_current_weather_spoken(self):
        # Test generating spoken weather description with IP address
        url = f'{self.base_url}/generate-current-weather-spoken'
        response = requests.post(url, json={"ip": "130.223.251.132"})
        self.assertEqual(response.status_code, 200)
    
    def test_generate_weather_spoken_from_text_missing_text(self):
        # Test generating spoken weather description from text
        url = f'{self.base_url}/generate-weather-spoken-from-text'
        response = requests.post(url, json={})
        self.assertEqual(response.status_code, 400)
    
    def test_generate_weather_spoken_from_text(self):
        # Test generating spoken weather description from text
        url = f'{self.base_url}/generate-weather-spoken-from-text'
        response = requests.post(url, json={"text": "Very low air humidity inside the building"})
        with open('/tmp/cloud_test.mp3', 'wb') as f:
            f.write(response.content)
        self.assertEqual(response.status_code, 200)
        
    def test_fetch_bigquery_history(self):
        url = f'{self.base_url}/fetch-bigquery-history'
        response = requests.post(url)
        self.assertEqual(response.status_code, 200)
        

if __name__ == '__main__':
    unittest.main()
