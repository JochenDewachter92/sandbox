import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")

if not subscription_key:
    raise RuntimeError(
        "AZURE_OPENAI_API_KEY is not set. Add it to your environment or a .env file next to main.py."
    )

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="https://joche-mhncioer-swedencentral.cognitiveservices.azure.com/",
    api_key=subscription_key,
)

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "role": "user",
            "content": "I am going to Paris, what should I see?",
        }
    ],
    max_tokens=4096,
    temperature=1.0,
    top_p=1.0,
    model=model_name
)

print(response.choices[0].message.content)