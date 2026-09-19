import os
import dotenv
from google import genai

# Load environment variables from .env file
dotenv.load_dotenv()

# Initialize Gemini client using GEMINI_API_KEY from environment
client = genai.Client()

# Generate content
response = client.interactions.create(
    model="gemini-3.6-flash",
    input="Say hello in one sentence."
)

print(response.output_text)

