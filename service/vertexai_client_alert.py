
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
import os

PROJECT_ID = os.getenv('PROJECT_ID')
PROJECT_LOCATION = os.getenv('PROJECT_LOCATION')
SYSTEM_INSTRUCTION = """This transformer takes future weather conditions (in 6 hours) (including temperature, weather condition, humidity, wind speed, and others) as inputs. 
It processes these inputs to generate a text description of the future weather. The description includes recommending appropriate clothing and activities based on the forecasted conditions and time.
For example, if it is going to be cold, advise wearing a jacket and suggest going to a restaurant to drink hot chocolate, or if it is going to rain in the morning, suggest taking an umbrella and visiting a museum. 
The advice is given in a serious tone. The generated text is crafted to be phonetically clear and simple, making it ideal for text-to-speech applications. No longer than 50 words. No emojis, special characters, or HTML tags."""

class VertexAIClientAltert:
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
        