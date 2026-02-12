import os
import json
import feedparser
from google import genai
from google.genai import types

# 1. Configuration - Add any founder RSS feeds here
FOUNDER_FEEDS = [
    {"name": "Paul Graham", "url": "http://www.aaronsw.com/2002/feeds/pgessays.rss"},
    {"name": "Sam Altman", "url": "https://blog.samaltman.com/posts.atom"},
    {"name": "Naval Ravikant", "url": "https://nav.al/feed"}
]

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY_FOUNDERS"))

def get_high_signal_summary(title, link, founder_name):
    """Uses Gemini 2.5 to decide if we should 'sprinkle' this article."""
    prompt = f"""
    You are a world-class startup mentor. Analyze this article title: "{title}" by {founder_name}.
    1. Is this 'High Signal' for a student/entrepreneur? (Yes/No)
    2. Provide a 1-sentence 'hook' summary.
    3. Return JSON format: {{"high_signal": bool, "summary": "string"}}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except:
        return {"high_signal": False, "summary": ""}

def curate():
    new_articles = []
    
    # Load existing to avoid duplicates
    if os.path.exists("founder_articles.json"):
        with open("founder_articles.json", "r") as f:
            existing_articles = json.load(f)
            existing_urls = {a['url'] for a in existing_articles}
    else:
        existing_articles = []
        existing_urls = set()

    for feed in FOUNDER_FEEDS:
        print(f"Checking {feed['name']}...")
        parsed = feedparser.parse(feed['url'])
        
        # Only check the latest 3 entries to save API tokens
        for entry in parsed.entries[:3]:
            if entry.link not in existing_urls:
                analysis = get_high_signal_summary(entry.title, entry.link, feed['name'])
                
                if analysis.get("high_signal"):
                    new_articles.append({
                        "title": entry.title,
                        "url": entry.link,
                        "snippet": analysis.get("summary"),
                        "founder_name": feed['name'],
                        "image": "https://images.unsplash.com/photo-1519389950473-47ba0277781c", # Default placeholder
                        "timestamp": entry.get("published", "")
                    })

    # Combine and save (Keep only the latest 50 to keep the file small)
    final_list = (new_articles + existing_articles)[:50]
    with open("founder_articles.json", "w") as f:
        json.dump(final_list, f, indent=4)
    print(f"Added {len(new_articles)} new high-signal articles!")

if __name__ == "__main__":
    curate()
