import os
import traceback
from flask import Flask, jsonify, request
from google import genai
from google.genai import types

app = Flask(__name__)

# 1. Initialize the client using the API key from environment variables
# Note: The SDK handles the endpoint internally, no need for GEMINI_ENDPOINT string
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.route("/")
def home():
    return "<h1>The Quote Fountain is Alive!</h1>"

@app.route("/quote", methods=["GET"])
def get_quote():
    # Check if API Key exists
    if not os.getenv("GEMINI_API_KEY"):
        return jsonify({"error": "GEMINI_API_KEY environment variable is missing"}), 500

    try:
        # 2. Call Gemini 3 Flash Preview using the SDK's native methods
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents="Give me a unique and thought-provoking quote for today.",
            config=types.GenerateContentConfig(
                # Low thinking level keeps it fast for a simple quote generator
                thinking_config=types.ThinkingConfig(
                    thinking_level="low" 
                ) 
            )
        )

        # 3. Use the SDK's built-in .text property to get the quote
        # The SDK handles parsing the JSON for you!
        quote = response.text
        
        return jsonify({"quote": quote.strip()})

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/summarize", methods=["POST"])
def summarize():
    article_url = request.json.get("url")
    
    prompt = f"Analyze the content at this URL and provide a 3-bullet point summary focusing on core technical or business takeaways: {article_url}"
    
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="low") 
            )
        )
        return jsonify({"summary": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
if __name__ == '__main__':
    app.run(debug=True)
