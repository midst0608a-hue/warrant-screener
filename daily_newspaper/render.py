"""
Rendering Engine Module (Render)
Injects Gemini curated JSON data into Jinja2 newspaper template to generate final static HTML.
"""

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_taiwan_weekday(dt: datetime) -> str:
    weekdays = ["星期一 (Monday)", "星期二 (Tuesday)", "星期三 (Wednesday)", 
                "星期四 (Thursday)", "星期五 (Friday)", "星期六 (Saturday)", "星期日 (Sunday)"]
    return weekdays[dt.weekday()]


def calculate_edition_info(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """Generates dynamic volume and issue numbers based on calendar."""
    if dt is None:
        # Taiwan Time UTC+8
        dt = datetime.now(timezone(timedelta(hours=8)))
        
    year = dt.year
    volume = year - 1920  # e.g., Vol. 106 in 2026
    issue = dt.timetuple().tm_yday  # Day of the year
    
    date_display = dt.strftime("%Y 年 %m 月 %d 日")
    
    return {
        "date_display": date_display,
        "weekday": get_taiwan_weekday(dt),
        "volume": volume,
        "issue": issue,
        "iso_date": dt.strftime("%Y-%m-%d")
    }


def render_newspaper_html(curated_data: Dict[str, Any], config: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Renders curated news data into a static HTML newspaper page.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Initialize Jinja2 Environment
    env = Environment(
        loader=FileSystemLoader(script_dir),
        autoescape=select_autoescape(["html", "xml"])
    )
    
    template = env.get_template("template.html")
    
    # Context assembly
    now_tpe = datetime.now(timezone(timedelta(hours=8)))
    edition_info = calculate_edition_info(now_tpe)
    
    api_key = os.environ.get("GEMINI_API_KEY") or config.get("gemini", {}).get("api_key", "")
    
    context = {
        "newspaper": config.get("newspaper", {}),
        "gemini_model": config.get("gemini", {}).get("model", "gemini-2.5-flash"),
        "api_key": api_key,
        "date_str": edition_info["date_display"],
        "generated_time": now_tpe.strftime("%Y-%m-%d %H:%M:%S (UTC+8)"),
        "edition_info": edition_info,
        "headline": curated_data.get("headline", {}),
        "columns": curated_data.get("columns", []),
        "stock_market": curated_data.get("stock_market", []),
        "sidebar": curated_data.get("sidebar", []),
        "editorial": curated_data.get("editorial", {}),
        "user_editorial_feedback": config.get("user_editorial_feedback", ""),
        "market_pulse": curated_data.get("market_pulse", {
            "sentiment": "多元交融",
            "watch_topics": ["#科技前沿", "#全球財經", "#總體趨勢"]
        }),
        "curated_edition_json": json.dumps(curated_data, ensure_ascii=False)
    }
    
    rendered_html = template.render(context)
    
    if output_path is None:
        out_filename = config.get("output_filename", "newspaper.html")
        output_path = os.path.join(script_dir, out_filename)
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)
        
    logger.info(f"Newspaper successfully generated at: {output_path}")
    return output_path


if __name__ == "__main__":
    from summarizer import create_mock_newspaper
    
    cfg_file = os.path.join(os.path.dirname(__file__), "config.json")
    with open(cfg_file, "r", encoding="utf-8") as f:
        cfg = json.load(f)
        
    mock_data = create_mock_newspaper([], cfg)
    out_file = render_newspaper_html(mock_data, cfg)
    print(f"Rendered test newspaper: {out_file}")
