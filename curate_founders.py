import os
import json
import sys
from google import genai
from google.genai import types

# Configuration: Mentors for Gemini to track
FOUNDERS = ["Paul Graham", "Sam Altman", "Naval Ravikant", "Vitalik Buterin", "Marc Andreessen"]

# Map secret to variable used in script
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ FATAL: GEMINI_API_KEY is not set.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

def search_and_curate_founder_content(founder_name):
    """Uses Gemini Search Tool to find the absolute latest from a founder."""
    prompt = f"""
    Search for the latest articles, essays, or significant blog posts written by {founder_name} in the last 30 days.
    For each valid finding:
    1. Verify it is actually written by them.
    2. Write a 1-sentence high-signal 'hook' summary.
    3. Return a list of JSON objects: {{"title": "str", "url": "str", "snippet": "str", "founder_name": "{founder_name}", "image": "str"}}
    Limit to the top 2 most relevant new findings.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(googleSearch=types.GoogleSearch())],
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_budget=-1)
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"⚠️ Error searching for {founder_name}: {e}")
        return []

def curate():
    # 1. Load Current Feed and Archive
    current_feed_path = "founder_articles.json"
    archive_path = "older_articles.json"
    
    def load_json(path):
        if os.path.exists(path):
            with open(path, "r") as f: return json.load(f)
        return []

    existing_articles = load_json(current_feed_path)
    older_articles = load_json(archive_path)
    
    existing_urls = {a['url'] for a in existing_articles} | {a['url'] for a in older_articles}
    
    # 2. Hunt for new content
    newly_found = []
    for founder in FOUNDERS:
        print(f"🔍 Gemini is searching for {founder}...")
        results = search_and_curate_founder_content(founder)
        for item in results:
            if item['url'] not in existing_urls:
                newly_found.append(item)

    if not newly_found:
        print("✅ No new articles found today.")
        return

    # 3. Rolling Archive Logic
    # Move 'old' current articles to archive, then add new ones to top
    updated_archive = newly_found + existing_articles + older_articles
    
    # Keep the current feed 'Fresh' (Top 20)
    current_feed = (newly_found + existing_articles)[:20]
    
    # Keep the archive robust (Top 500)
    archive_feed = updated_archive[:500]

    # 4. Save files
    with open(current_feed_path, "w") as f:
        json.dump(current_feed, f, indent=4)
        
    with open(archive_path, "w") as f:
        json.dump(archive_feed, f, indent=4)

    print(f"🚀 Success! Added {len(newly_found)} new articles to the feed.")

if __name__ == "__main__":
    curate()
