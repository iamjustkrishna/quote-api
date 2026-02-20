import os
import traceback
from flask import Flask, jsonify, request
from google import genai
from google.genai import types

app = Flask(__name__)

# 1. Initialize the client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Shared configuration from your 2.5 snippet
# thinking_budget=-1 allows the model maximum reasoning capacity
tools = [types.Tool(googleSearch=types.GoogleSearch())]
thinking_config = types.ThinkingConfig(thinking_budget=-1)

@app.route("/")
def home():
    return "<h1>The Quote Fountain is Alive!</h1>"

@app.route("/quote", methods=["GET"])
def get_quote():
    if not os.getenv("GEMINI_API_KEY"):
        return jsonify({"error": "GEMINI_API_KEY is missing"}), 500

    try:
        # Using 2.5 Flash for the daily quote
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents="Give me a unique and thought-provoking quote for today.",
            config=types.GenerateContentConfig(
                thinking_config=thinking_config
            )
        )
        
        return jsonify({"quote": response.text.strip()})

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/summarize", methods=["POST"])
def summarize():
    try:
        data = request.get_json() 
        if not data or "url" not in data:
            return jsonify({"error": "No URL provided"}), 400
            
        article_url = data.get("url")
        
        # Enhanced prompt for Persona's Knowledge Vault
        prompt = (
            f"Provide a high-level, 3-bullet point summary of this article "
            f"for a student's knowledge vault. Use the Google Search tool "
            f"to verify facts or add context if necessary: {article_url}"
        )
        
        # Calling Gemini 2.5 Flash with Thinking and Google Search tools
        response = client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=thinking_config,
                tools=tools # Includes Google Search
            )
        )
        
        return jsonify({"summary": response.text})

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Using threaded=True is helpful when handling AI requests
    app.run(debug=True, threaded=True)
