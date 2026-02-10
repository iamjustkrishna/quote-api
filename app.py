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
    try:
        # Get the JSON data sent from Retrofit
        data = request.get_json() 
        
        if not data or "url" not in data:
            return jsonify({"error": "No URL provided in the request body"}), 400
            
        article_url = data.get("url")
        
        # High-impact prompt for Persona's "Study" focus
        prompt = (
            f"Please provide a high-level, 3-bullet point summary of this article "
            f"for a student's personal knowledge vault. Focus on the 'why it matters' "
            f"and 'key takeaway': {article_url}"
        )
        
        # Calling Gemini 3 Flash Preview
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="low") 
            )
        )
        
        return jsonify({"summary": response.text})

    except Exception as e:
        # This helps you debug in the terminal if something else goes wrong
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
        
if __name__ == '__main__':
    app.run(debug=True)
