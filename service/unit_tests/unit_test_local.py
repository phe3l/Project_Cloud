import unittest, os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

class ServiceTestLocal(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_insert_weather(self):
        # Test sending data to BigQuery
        response = self.client.post('/send-to-bigquery', json={"values": {"date": "2024-05-01", "time": "17:29:54", "indoor_temp": 28.0, "indoor_humidity": 39.0, "outdoor_temp": 21.9, "outdoor_humidity": 28.0, "outdoor_weather": "Test", "ip_address": "86.111.136.24"}})
        self.assertEqual(response.status_code, 200)

    def test_get_current_weather_missing_ip(self):
        # Test getting current weather without IP address
        response = self.client.post('/current-weather', json={})
        self.assertEqual(response.status_code, 400)

    def test_get_current_weather(self):
        # Test getting current weather with IP address
        response = self.client.post('/current-weather', json={"ip": "130.223.251.132"})
        self.assertEqual(response.status_code, 200)

    def test_get_future_weather(self):
        # Test getting future weather
        response = self.client.post('/future-weather', json={"ip": "130.223.251.132"})
        self.assertEqual(response.status_code, 200)
        
    def test_generate_current_weather_spoken_missing_ip(self):
        # Test generating spoken weather description without IP address
        response = self.client.post('/generate-current-weather-spoken', json={})
        self.assertEqual(response.status_code, 400)

    def test_generate_current_weather_spoken(self):
        # Test generating spoken weather description with IP address
        response = self.client.post('/generate-current-weather-spoken', json={"ip": "130.223.251.132"})
        self.assertEqual(response.status_code, 200)
    
    def test_generate_weather_spoken_from_text_missing_text(self):
        # Test generating spoken weather description from text
        response = self.client.post('/generate-weather-spoken-from-text', json={})
        self.assertEqual(response.status_code, 400)
    
    def test_generate_weather_spoken_from_text(self):
        # Test generating spoken weather description from text
        response = self.client.post('/generate-weather-spoken-from-text', json={"text": "Very low air humidity inside the building"})
        self.assertEqual(response.status_code, 200)
        
    def test_fetch_bigquery_history(self):
        # Test fetching weather data from BigQuery
        response = self.client.post('/fetch-bigquery-history')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
