from google import genai

client = genai.Client()  # reads GEMINI_API_KEY from env automatically

# To this:
interaction = client.interactions.create(
    model="gemini-3.6-flash",
    # ... other arguments
    input="Say hello in one sentence."
)

print(interaction.output_text)
