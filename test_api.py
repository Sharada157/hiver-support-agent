import os
import dotenv
from google import genai

# Load environment variables from .env file
dotenv.load_dotenv()

# Initialize Gemini client using GEMINI_API_KEY from environment
client = genai.Client()

# Generate content
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say hello in one sentence."
)

print(response.text)

