"""
Information Ingestion Module (Fetcher)
Handles RSS feeds scraping, date filtering, and HTML text cleaning.
"""

import json
import logging
import re
import sys
import html
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
import feedparser
import requests
import warnings
from dateutil import parser as date_parser
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 DailyNewspaper/1.0"


def clean_html(raw_html: str) -> str:
    """Removes HTML tags, extra whitespace, and decodes entities."""
    if not raw_html:
        return ""
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "iframe"]):
            element.decompose()
        text = soup.get_text(separator=" ", strip=True)
    except Exception:
        # Fallback regex
        text = re.sub(r"<[^>]+>", "", raw_html)
    
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_datetime(entry: Dict[str, Any]) -> Optional[datetime]:
    """Extracts and parses publication date to a timezone-aware UTC datetime."""
    # 1. Try feedparser parsed tuple
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass
            
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass

    # 2. Try raw date strings
    for field in ["published", "pubDate", "updated", "date", "dc:date"]:
        val = entry.get(field)
        if val and isinstance(val, str):
            try:
                dt = date_parser.parse(val)
                if dt.tzinfo is None:
                    # Assume UTC if naive
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                return dt
            except Exception:
                continue

    return None


def fetch_feed_entries(feed_info: Dict[str, str], timeout: int = 10) -> List[Dict[str, Any]]:
    """Fetches and parses a single RSS feed."""
    url = feed_info.get("url", "")
    source_name = feed_info.get("name", "Unknown Source")
    category = feed_info.get("category", "General")

    logger.info(f"Fetching RSS: {source_name} ({url})")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    content = None
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            content = response.content
        else:
            logger.warning(f"Status code {response.status_code} for {url}, falling back to direct url parse")
            content = url
    except Exception as e:
        logger.warning(f"Requests failed for {url} ({e}), trying feedparser direct parse...")
        content = url

    parsed = feedparser.parse(content)
    if parsed.bozo and not parsed.entries:
        logger.warning(f"Failed to parse feed {source_name}: {parsed.get('bozo_exception')}")
        return []

    results = []
    for entry in parsed.entries:
        title = clean_html(entry.get("title", "")).strip()
        link = entry.get("link", "").strip()
        
        # Summary/content extraction
        raw_content = ""
        if "content" in entry and entry.content:
            raw_content = entry.content[0].get("value", "")
        elif "summary" in entry:
            raw_content = entry.get("summary", "")
        elif "description" in entry:
            raw_content = entry.get("description", "")
            
        summary = clean_html(raw_content)
        
        # Limit summary length to prevent bloated context
        if len(summary) > 400:
            summary = summary[:400] + "..."
            
        pub_dt = parse_datetime(entry)
        
        if not title or not link:
            continue
            
        results.append({
            "source": source_name,
            "category": category,
            "title": title,
            "link": link,
            "summary": summary,
            "published_at": pub_dt.isoformat() if pub_dt else None,
            "pub_dt": pub_dt
        })
        
    return results


def fetch_all_news(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetches news from all configured RSS feeds, filters them by publication time,
    and applies balanced source interleaving to ensure high topic and media diversity.
    """
    rss_feeds = config.get("rss_feeds", [])
    filter_hours = config.get("filter_hours", 36)
    now_utc = datetime.now(timezone.utc)
    cutoff_time = now_utc - timedelta(hours=filter_hours)
    
    feed_buckets = []
    seen_titles = set()
    
    for feed in rss_feeds:
        feed_articles = []
        try:
            entries = fetch_feed_entries(feed)
            for item in entries:
                # Deduplication by title
                normalized_title = re.sub(r"[\s\W_]+", "", item["title"])
                if normalized_title in seen_titles:
                    continue
                seen_titles.add(normalized_title)
                
                # Filter by publication time if available
                pub_dt = item.get("pub_dt")
                if pub_dt:
                    if pub_dt >= cutoff_time:
                        feed_articles.append(item)
                else:
                    feed_articles.append(item)
        except Exception as e:
            logger.error(f"Error fetching feed {feed.get('name')}: {e}")

        if feed_articles:
            # Cap each single feed to prevent one source from monopolizing
            feed_buckets.append(feed_articles[:8])

    # Round-robin interleaving across different feeds to ensure high diversity
    all_articles = []
    max_len = max((len(b) for b in feed_buckets), default=0)
    for idx in range(max_len):
        for bucket in feed_buckets:
            if idx < len(bucket):
                all_articles.append(bucket[idx])

    # Clean temporary datetime object
    for art in all_articles:
        art.pop("pub_dt", None)

    logger.info(f"Total balanced articles prepared across {len(feed_buckets)} diverse sources: {len(all_articles)}")
    return all_articles


if __name__ == "__main__":
    import os
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    
    news = fetch_all_news(cfg)
    print(f"Sample fetched article count: {len(news)}")
    if news:
        print("First article sample:", json.dumps(news[0], ensure_ascii=False, indent=2))
