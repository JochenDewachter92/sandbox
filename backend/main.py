import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

import dotenv
dotenv.load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
CHATKIT_WORKFLOW_ID = os.environ["CHATKIT_WORKFLOW_ID"]

app = FastAPI()

# Allow your React dev server to call this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SessionResponse(BaseModel):
    client_secret: str

@app.post("/api/chatkit/session", response_model=SessionResponse)
def create_chatkit_session():
    """
    Minimal session creation.
    This is where you bind ChatKit to your Agent Builder workflow.
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'OpenAI-Beta': 'chatkit_beta=v1'  # Required beta header
    }

    payload = {
        'workflow': {
            'id': CHATKIT_WORKFLOW_ID  # <-- Agent Builder workflow
        },
        'user': 'demo-user-123'  # any stable per-user identifier
    }

    response = requests.post(
        'https://api.openai.com/v1/chatkit/sessions',
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code != 200:
        raise Exception(f'API Error: {response.text}')

    session = response.json()
    
    # The client_secret is what the frontend will use
    return SessionResponse(client_secret=session['client_secret'])

#    uv run uvicorn main:app --reload --port 8001