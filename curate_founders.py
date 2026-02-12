import os
import json
import sys
import feedparser
import time
from google import genai
from google.genai import types

# 1. Configuration: RSS Feeds for stable tracking
FOUNDER_FEEDS = [
    {"name": "Paul Graham", "url": "http://www.aaronsw.com/2002/feeds/pgessays.rss"},
    {"name": "Sam Altman", "url": "https://blog.samaltman.com/posts.atom"},
    {"name": "Naval Ravikant", "url": "https://nav.al/feed"},
    {"name": "Vitalik Buterin", "url": "https://vitalik.eth.limo/feed.xml"},
    {"name": "Marc Andreessen", "url": "https://pmarca-archive.cc/feed/"}
]

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ FATAL: GEMINI_API_KEY is not set.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

def get_ai_hook(title, founder_name):
    """Uses Gemini to write a high-signal 1-sentence hook for the feed."""
    prompt = f"Write a 1-sentence 'hook' summary for an article titled '{title}' by {founder_name}. Focus on why a student entrepreneur should read it. Keep it punchy."
    try:
        # We use a simple text call here - much cheaper/faster than Search
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ AI Hook failed: {e}")
        return "Insightful essay on startups and technology."

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        except: return []
    return []

def curate():
    current_feed_path = "founder_articles.json"
    archive_path = "older_articles.json"

    existing_articles = load_json(current_feed_path)
    older_articles = load_json(archive_path)
    existing_urls = {a['url'] for a in existing_articles} | {a['url'] for a in older_articles}

    newly_found = []

    for feed in FOUNDER_FEEDS:
        print(f"📡 Parsing RSS for {feed['name']}...")
        parsed = feedparser.parse(feed['url'])
        
        # Check top 3 latest entries per founder
        for entry in parsed.entries[:3]:
            link = entry.link
            if link not in existing_urls:
                print(f"✨ New article found: {entry.title}")
                hook = get_ai_hook(entry.title, feed['name'])
                
                newly_found.append({
                    "title": entry.title,
                    "url": link,
                    "snippet": hook,
                    "founder_name": feed['name'],
                    "image": "https://images.unsplash.com/photo-1519389950473-47ba0277781c", # High-quality default
                    "timestamp": time.time()
                })
                # Small sleep to prevent hitting Gemini RPM limits
                time.sleep(2)

    if not newly_found:
        print("✅ Everything is up to date.")
        return

    # Rolling Archive Logic
    all_articles = newly_found + existing_articles + older_articles
    current_feed = (newly_found + existing_articles)[:25] # Fresh list
    archive_feed = all_articles[:500] # Full history

    with open(current_feed_path, "w") as f:
        json.dump(current_feed, f, indent=4)
    with open(archive_path, "w") as f:
        json.dump(archive_feed, f, indent=4)

    print(f"🚀 Success! Added {len(newly_found)} new articles.")

if __name__ == "__main__":
    curate()
