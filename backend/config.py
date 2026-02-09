"""
Backend Configuration

Loads environment variables and provides configuration settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env.local first (for local development), then .env as fallback
env_local = Path(__file__).parent / '.env.local'
env_file = Path(__file__).parent / '.env'

if env_local.exists():
    load_dotenv(env_local)
elif env_file.exists():
    load_dotenv(env_file)

# Gemini API Key
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GEMINI_API_KEY:
    print("=" * 60)
    print("⚠️  WARNING: GOOGLE_API_KEY not found!")
    print("   AI-powered coaching features will use fallback mode.")
    print("   To enable Gemini AI:")
    print("   1. Get a key from: https://aistudio.google.com/")
    print("   2. Add to backend/.env.local: GOOGLE_API_KEY=your_key")
    print("=" * 60)

# MongoDB Config
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "idolcode")

# Server Config
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
