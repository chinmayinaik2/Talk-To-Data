# Talk-to-Data Readiness Kit

A five-hour prototype for assessing semantic-model readiness using the supplied synthetic starter kit.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and optionally add a Gemini API key.
4. Run: `streamlit run app.py`

The core scanner and scoring engine will work without an API key. Never place real customer data or secrets in prompts.

## Starter kit

The original Theme 04 starter kit is included under `data/starter_kit/`. See its README and model definition for the exact requirements and known model issues.
