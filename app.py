from flask import Flask, jsonify
import requests
import os
from google import genai
from google.genai import types

app = Flask(__name__)

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.route("/")
def home():
    return "<h1>The Quote Fountain is Alive!</h1>"

@app.route("/quote", methods=["GET"])
def get_quote():
    if not GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY is missing"}), 500

    try:
        response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents="Give me a unique and thought-provoking quote for today.",
        config=types.GenerateContentConfig(
            # Gemini 3 introduces thinking levels: 'low' for speed, 'high' for complex reasoning
            thinking_config=types.ThinkingConfig(thinking_level="low") 
        )
    )
        response.raise_for_status()
        data = response.json()
        quote = data['candidates'][0]['content']['parts'][0]['text']
        return jsonify({"quote": quote})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
