import os
import json
import sys
import feedparser
import time
from google import genai
from google.genai import types

# 1. Expanded Founder Feeds (Robust & High-Signal for Persona)
FOUNDER_FEEDS = [
    {"name": "Paul Graham", "url": "http://www.aaronsw.com/2002/feeds/pgessays.rss"},
    {"name": "Sam Altman", "url": "https://blog.samaltman.com/posts.atom"},
    {"name": "Naval Ravikant", "url": "https://nav.al/feed"},
    {"name": "Vitalik Buterin", "url": "https://vitalik.eth.limo/feed.xml"},
    {"name": "Marc Andreessen", "url": "https://pmarca-archive.cc/feed/"},
    {"name": "Lenny Rachitsky", "url": "https://www.lennysnewsletter.com/feed"},
    {"name": "Garry Tan", "url": "https://garrytan.com/feed.xml"},
    {"name": "a16z", "url": "https://a16z.com/feed/"}
]

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ FATAL: GEMINI_API_KEY is not set.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

def load_json(path):
    """Safely loads JSON, creating an empty list if the file doesn't exist or is corrupted."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        except Exception as e:
            print(f"⚠️ Warning: Could not read {path} ({e}). Starting fresh.")
            return []
    return []

def save_json(path, data):
    """Safely writes data to JSON."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ FATAL: Failed to save to {path}: {e}")

def batch_summarize(articles):
    """Summarizes multiple articles in ONE single Gemini API call to save time and limits."""
    if not articles:
        return []
    
    prompt_items = []
    for i, a in enumerate(articles):
        prompt_items.append(f"<article id='{i}'>\nTitle: {a['title']}\n</article>")

    prompt = f"""
    You are curating content for student entrepreneurs. 
    For each article below, provide:
    1. A 'snippet': A punchy 1-sentence hook.
    2. A 'summary': A 3-sentence detailed breakdown.

    Return ONLY a valid JSON array of objects with keys: "id", "snippet", "summary".
    
    Articles:
    {chr(10).join(prompt_items)}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", # Fast and cost-effective
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3 # Keep it focused, less hallucination
            )
        )
        
        ai_data = json.loads(response.text)
        
        # Merge AI results back into the articles
        for item in ai_data:
            idx = int(item['id'])
            articles[idx]['snippet'] = item.get('snippet', 'Insightful read for founders.')
            articles[idx]['summary'] = item.get('summary', 'Detailed analysis is being processed.')
            
        return articles
    except Exception as e:
        print(f"⚠️ Batch AI failed: {e}")
        # Fallback to prevent data loss if Gemini fails
        for a in articles:
            a['snippet'] = "New insight for your founder journey."
            a['summary'] = "Read the full article to learn more."
        return articles

def curate():
    # Use the unified naming convention
    current_feed_path = "summary_articles.json"
    archive_path = "older_articles.json"

    existing_articles = load_json(current_feed_path)
    older_articles = load_json(archive_path)
    
    # Use .get('url') safely in case old data is missing the key
    existing_urls = {a.get('url') for a in existing_articles if a.get('url')} | \
                    {a.get('url') for a in older_articles if a.get('url')}

    newly_found = []

    for feed in FOUNDER_FEEDS:
        print(f"📡 Parsing RSS for {feed['name']}...")
        parsed = feedparser.parse(feed['url'])
        
        # Check top 3 latest entries per founder
        for entry in parsed.entries[:3]:
            link = entry.link
            if link not in existing_urls:
                print(f"✨ New article found: {entry.title}")
                newly_found.append({
                    "title": entry.title,
                    "url": link,
                    "founder_name": feed['name'],
                    "image": "https://images.unsplash.com/photo-1519389950473-47ba0277781c",
                    "timestamp": time.time(),
                    # Snippet and summary will be populated by AI
                    "snippet": "",
                    "summary": ""
                })

    if not newly_found:
        print("✅ Everything is up to date.")
        return

    # Process AI summaries in batches of 5 to stay well within API limits
    print(f"🧠 Processing {len(newly_found)} new articles via Gemini...")
    fully_processed = []
    for i in range(0, len(newly_found), 5):
        batch = newly_found[i:i+5]
        fully_processed.extend(batch_summarize(batch))
        time.sleep(2) # Brief pause to respect rate limits

    # Rolling Archive Logic
    all_articles = fully_processed + existing_articles + older_articles
    
    # Keep the main feed to the 30 freshest articles
    current_feed = all_articles[:30] 
    # Store everything else in the archive
    archive_feed = all_articles[30:500] 

    # Save files
    save_json(current_feed_path, current_feed)
    save_json(archive_path, archive_feed)

    print(f"🚀 Success! {len(fully_processed)} new articles added and JSON updated.")

if __name__ == "__main__":
    curate()
