
import os
from dotenv import load_dotenv
from google import genai

# Load environment variables from the project root
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.8-flash"


def generate_text(prompt: str) -> str:
    """
    Send a prompt to Gemini and return its text response.
    Raises a clear error if configuration or API access fails.
    """

    if not API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is missing. Check your .env file."
        )

    client = genai.Client(api_key=API_KEY)

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        return response.text

    finally:
        client.close()
