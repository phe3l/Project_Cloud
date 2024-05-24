
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
import os

PROJECT_ID = os.getenv('PROJECT_ID')
PROJECT_LOCATION = os.getenv('PROJECT_LOCATION')

class VertexAIClient:
    def __init__(self) -> None:
        
        vertexai.init(project=PROJECT_ID, location=PROJECT_LOCATION)
        

    def get_weather_description(self, weather_data: dict, system_instruction: str) -> str:
        """Generate a playful and engaging text description of the weather."""
        try:
            model = GenerativeModel(model_name='gemini-1.5-pro-preview-0409', system_instruction=system_instruction)
            chat = model.start_chat()
            response = chat.send_message(weather_data)
            return response.text
        except Exception as e:
            raise Exception(f"Failed to generate weather description: {e}")
        