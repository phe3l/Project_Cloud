
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
import os

PROJECT_ID = os.getenv('PROJECT_ID')
PROJECT_LOCATION = os.getenv('PROJECT_LOCATION')
SYSTEM_INSTRUCTION = """This transformer takes weather conditions (might include temperature, weather condition, humidity, wind speed and others) as inputs. 
                    It processes these inputs to generate a PLAYFUL and engaging text description of the weather.
                    It makes it lyrical and engaging, with a touch of humor.
                    The generated text is crafted to be phonetically clear and simple, making it ideal for text-to-speech applications. 
                    No longer then 50 words. No emojis, special characters, or HTML tags."""

class VertexAIClient:
    def __init__(self) -> None:
        
        vertexai.init(project=PROJECT_ID, location=PROJECT_LOCATION)
        
        self.model = GenerativeModel(model_name='gemini-1.5-pro-preview-0409', system_instruction=SYSTEM_INSTRUCTION)
        self.chat = self.model.start_chat()
        
        
    def get_weather_description(self, weather_data: dict) -> str:
        """Generate a playful and engaging text description of the weather."""
        try:
            
            response = self.chat.send_message(weather_data)
            return response.text
        
        except Exception as e:
            raise Exception(f"Failed to generate weather description: {e}")
        