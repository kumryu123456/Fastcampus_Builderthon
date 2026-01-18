"""
List available Gemini models for the current SDK version.
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file
load_dotenv()

# Get API key from environment
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_API_KEY not found in environment")
    print("Please set it in your .env file")
    exit(1)

# Configure API
genai.configure(api_key=api_key)

print("=== Available Gemini Models ===\n")

try:
    # List all available models
    for model in genai.list_models():
        # Only show models that support generateContent
        if 'generateContent' in model.supported_generation_methods:
            print(f"Model: {model.name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Description: {model.description}")
            print(f"  Supported: {model.supported_generation_methods}")
            print()
except Exception as e:
    print(f"Error listing models: {e}")
    print("\nTrying alternative approach...")

    # Try some common model names
    test_models = [
        "gemini-pro",
        "gemini-1.0-pro",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "models/gemini-pro",
        "models/gemini-1.0-pro",
        "models/gemini-1.5-pro",
        "models/gemini-1.5-flash",
    ]

    print("\nTesting model names:")
    for model_name in test_models:
        try:
            model = genai.GenerativeModel(model_name)
            print(f"✓ {model_name} - WORKS")
        except Exception as e:
            print(f"✗ {model_name} - FAILED: {str(e)[:60]}")
