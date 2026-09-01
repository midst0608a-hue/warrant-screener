"""
Daily Newspaper Generator Main Runner
Orchestrates: Fetching RSS -> Gemini Summarizing -> Jinja2 Rendering -> Browser Preview
"""

import os
import sys
import json
import argparse
import logging
import webbrowser
from pathlib import Path

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fetcher import fetch_all_news
from summarizer import curate_newspaper_with_gemini, create_mock_newspaper
from render import render_newspaper_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("DailyNewspaper")


def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        logger.error(f"Config file not found at: {config_path}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Daily Automated Newspaper Generator powered by Gemini & RSS")
    parser.add_argument("--config", "-c", default="config.json", help="Path to config.json")
    parser.add_argument("--output", "-o", default=None, help="Output HTML file path (default: newspaper.html)")
    parser.add_argument("--mock", action="store_true", help="Force use of mock summary data without calling Gemini API")
    parser.add_argument("--no-open", action="store_true", help="Do not automatically open browser after generation")
    parser.add_argument("--save-json", action="store_true", help="Save intermediate curated JSON to disk")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(base_dir, args.config) if not os.path.isabs(args.config) else args.config
    
    print("\n" + "=" * 60)
    print(" 📰 每日新聞報紙生成器 (Daily Newspaper Generator)")
    print("=" * 60 + "\n")

    # 1. Load configuration
    logger.info("Loading configuration...")
    config = load_config(config_file)

    # 2. Fetch news
    logger.info("Step 1/3: Ingesting news from RSS feeds...")
    articles = fetch_all_news(config)
    logger.info(f"Retrieved {len(articles)} fresh articles.")

    # 3. Gemini curation
    logger.info("Step 2/3: Analyzing and curating newspaper content...")
    if args.mock:
        curated_data = create_mock_newspaper(articles, config)
    else:
        curated_data = curate_newspaper_with_gemini(articles, config)

    # Optionally save JSON
    if args.save_json or os.environ.get("SAVE_NEWSPAPER_JSON") == "1":
        json_out = os.path.join(base_dir, "curated_edition.json")
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(curated_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved curated edition JSON to {json_out}")

    # 4. Render HTML
    logger.info("Step 3/3: Rendering vintage broadsheet template...")
    out_file = args.output
    if out_file and not os.path.isabs(out_file):
        out_file = os.path.join(base_dir, out_file)
        
    final_html_path = render_newspaper_html(curated_data, config, out_file)

    print("\n" + "—" * 60)
    print(f"✨ 報紙產出成功！檔案路徑: {final_html_path}")
    print("—" * 60 + "\n")

    # 5. Open browser
    if not args.no_open and not os.environ.get("CI"):
        try:
            logger.info("Opening generated newspaper in web browser...")
            webbrowser.open(Path(final_html_path).as_uri())
        except Exception as e:
            logger.warning(f"Could not open browser automatically: {e}")


if __name__ == "__main__":
    main()
