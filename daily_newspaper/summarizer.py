"""
Gemini Intelligence & Editorial Module (Summarizer)
Uses google-genai SDK to analyze raw news articles and curate a structured newspaper edition.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


NEWSPAPER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "headline": {
            "type": "OBJECT",
            "properties": {
                "title": {"type": "STRING", "description": "醒目震撼的頭條新聞主標題（約 15-25 字）"},
                "subtitle": {"type": "STRING", "description": "精闢次標題或導言（約 20-30 字）"},
                "category": {"type": "STRING", "description": "分類標籤，例如：全球總經、科技前沿、地緣政局"},
                "summary": {"type": "STRING", "description": "核心事實摘要段落（約 120-180 字，客觀精煉）"},
                "key_points": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "3 個核心關鍵要點或數據分析"
                },
                "market_linkage": {
                    "type": "OBJECT",
                    "properties": {
                        "indicator_name": {"type": "STRING", "description": "關聯大宗商品/宏觀/科技指標（例如：布蘭特原油期貨 Brent Crude / 費城半導體 SOX / 美債10年期殖利率 / 美元指數）"},
                        "ten_day_trend": {"type": "STRING", "description": "近 10 日走勢與具體價位/幅度變動摘要（例如：近 10 日自 $72.3 攀升至 $78.1 (+8.0%)）"},
                        "spillover_effects": {"type": "STRING", "description": "對實體經濟、台股/美股產業鏈之連鎖效應（例如：油運費率暴漲、航空成本承壓、塑化利差受壓）"},
                        "deep_dive_query": {"type": "STRING", "description": "用於點擊生成深度特刊的關鍵字（例如：中東油運危機與原油供應鏈連鎖衝擊）"}
                    },
                    "description": "關聯的大宗商品/市場指標與近 10 日動態（選填）"
                },
                "source": {"type": "STRING", "description": "新聞來源媒體名稱"},
                "url": {"type": "STRING", "description": "原文網址連結"}
            },
            "required": ["title", "subtitle", "category", "summary", "key_points", "source", "url"]
        },
        "columns": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING", "description": "專欄新聞標題（約 12-20 字）"},
                    "category": {"type": "STRING", "description": "分類，如：科技/AI、總經金融、國際局勢、Web3"},
                    "summary": {"type": "STRING", "description": "2-3 句事實摘要（約 80-120 字）"},
                    "key_takeaway": {"type": "STRING", "description": "一句話產業影響或洞察（約 20-40 字）"},
                    "market_linkage": {
                        "type": "OBJECT",
                        "properties": {
                            "indicator_name": {"type": "STRING", "description": "關聯大宗商品/宏觀指標（例如：布蘭特原油期貨、紐約原油 WTI、黃金、十年期美債、台幣匯率、費城半導體）"},
                            "ten_day_trend": {"type": "STRING", "description": "近 10 日走勢與具體價位/幅度變動摘要（例如：近 10 日自 $72.3 上漲至 $78.1 (+8.0%)）"},
                            "spillover_effects": {"type": "STRING", "description": "連鎖市場效應與受衝擊/受惠產業族群分析"},
                            "deep_dive_query": {"type": "STRING", "description": "一鍵生成深度特刊關鍵詞（例如：荷姆茲海峽航運停滯對全球能源與台股供應鏈之衝擊）"}
                        },
                        "description": "若新聞涉及地緣/能源大宗/總經利率/半導體等，必須提供市場連鎖指標與 10 日走勢"
                    },
                    "source": {"type": "STRING", "description": "來源媒體"},
                    "url": {"type": "STRING", "description": "原文網址"}
                },
                "required": ["title", "category", "summary", "key_takeaway", "source", "url"]
            },
            "description": "4 到 6 則重要焦點新聞"
        },
        "stock_market": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING", "description": "股市新聞標題（包含個股或族群動能）"},
                    "market_tag": {"type": "STRING", "description": "市場標籤，如：台股焦點、美股動態、半導體族群、AI概念股"},
                    "summary": {"type": "STRING", "description": "行情變化、主要原因與法人觀點摘要（約 60-100 字）"},
                    "trend_signal": {"type": "STRING", "description": "一句話看盤或資金流向提示（約 15-30 字）"},
                    "source": {"type": "STRING", "description": "來源媒體"},
                    "url": {"type": "STRING", "description": "原文網址"}
                },
                "required": ["title", "market_tag", "summary", "trend_signal", "source", "url"]
            },
            "description": "精選 3 則關鍵股市/產業行情/重磅個股新聞"
        },
        "sidebar": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING", "description": "簡訊標題（簡短有力）"},
                    "category": {"type": "STRING", "description": "分類標籤"},
                    "brief": {"type": "STRING", "description": "一到兩句快訊內文（約 40-70 字）"},
                    "source": {"type": "STRING", "description": "來源媒體"},
                    "url": {"type": "STRING", "description": "原文網址"}
                },
                "required": ["title", "category", "brief", "source", "url"]
            },
            "description": "4 到 6 則側欄全球簡訊與快訊"
        },
        "editorial": {
            "type": "OBJECT",
            "properties": {
                "title": {"type": "STRING", "description": "主筆銳評專欄標題（富有批判性與思辨深度）"},
                "author": {"type": "STRING", "description": "專欄作者署名，如：首席主筆 / Chief Columnist"},
                "commentary": {
                    "type": "STRING",
                    "description": "主筆冷眼/銳評內文（約 250-400 字，針對當日大事提供深度的洞察、利弊權衡與長遠觀點）"
                },
                "quote": {"type": "STRING", "description": "文中的精闢警句或金句"}
            },
            "required": ["title", "author", "commentary", "quote"]
        },
        "market_pulse": {
            "type": "OBJECT",
            "properties": {
                "sentiment": {"type": "STRING", "description": "今日市場與全球情緒（如：謹慎樂觀、科技狂潮、避險增溫等）"},
                "watch_topics": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "3-4 個今日核心關鍵字/話題標籤"
                }
            },
            "required": ["sentiment", "watch_topics"]
        }
    },
    "required": ["headline", "columns", "stock_market", "sidebar", "editorial", "market_pulse"]
}


def create_mock_newspaper(articles: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback generator in case Gemini API key is missing or network is unavailable."""
    logger.warning("Using Mock Newspaper Data for offline preview...")
    sample_arts = articles[:10] if articles else []
    
    headline_art = sample_arts[0] if len(sample_arts) > 0 else {
        "title": "全球半導體與 AI 算力基礎設施迎來新一輪擴張潮",
        "link": "https://technews.tw/",
        "source": "科技新報",
        "category": "科技與AI",
        "summary": "各大科技巨頭近期持續加大先進製程與資料中心投資，推動相關供應鏈營運動能強勁。"
    }
    
    cols = []
    for i, a in enumerate(sample_arts[1:6] if len(sample_arts) > 1 else []):
        cols.append({
            "title": a.get("title", f"重大市場動態報導第 {i+1} 則"),
            "category": a.get("category", "總經與財經"),
            "summary": a.get("summary", "新聞詳細內文重點摘要，包含產業變化與市場預期趨勢。")[:100],
            "key_takeaway": "持續觀察各國央行政策路徑與主要產業財報指引。",
            "source": a.get("source", "財經快訊"),
            "url": a.get("link", "#")
        })
        
    if not cols:
        cols = [
            {
                "title": "美歐通膨數據趨緩 降息路徑成為市場關注焦點",
                "category": "總經與財經",
                "summary": "全球主要經濟體通膨指標呈現漸進回落，市場對貨幣政策寬鬆週期的預期升溫，資金流向新興市場。",
                "key_takeaway": "實質利率下行有助於改善企業融資成本與流動性。",
                "source": "中央社",
                "url": "#"
            },
            {
                "title": "次世代開源模型推陳出新 企業端 AI 落地應用加速",
                "category": "科技與AI",
                "summary": "隨多模態大模型推理成本大幅下降，金融、製造與醫療垂直領域正快速導入自主化 AI 代理系統。",
                "key_takeaway": "技術競爭焦點由參數規模轉向高性價比之領域專用微調。",
                "source": "數位時代",
                "url": "#"
            }
        ]

    sidebars = []
    for i, a in enumerate(sample_arts[6:10] if len(sample_arts) > 6 else []):
        sidebars.append({
            "title": a.get("title", f"全球速覽快訊 {i+1}"),
            "category": a.get("category", "國際簡訊"),
            "brief": a.get("summary", "全球主要區域政經局勢與產業最新進展速讀。")[:60],
            "source": a.get("source", "國際編譯"),
            "url": a.get("link", "#")
        })
    if not sidebars:
        sidebars = [
            {"title": "原油期貨窄幅震盪", "category": "大宗商品", "brief": "產油國減產協議與全球需求預測拉鋸，能源價格維持區間走勢。", "source": "鉅亨網", "url": "#"},
            {"title": "加密資產機構資金穩定流入", "category": "Web3", "brief": "現貨 ETF 交易量平穩，鏈上活躍地址數創近期新高。", "source": "BlockTempo", "url": "#"},
            {"title": "綠色能源供應鏈法規更新", "category": "國際局勢", "brief": "歐盟發布新版碳邊境機制細則，跨國製造業加緊低碳轉型。", "source": "BBC 中文", "url": "#"}
        ]

    return {
        "headline": {
            "title": headline_art.get("title", "AI 算力競逐與新地緣經濟秩序成形"),
            "subtitle": "資本支出創新高之際，全球供應鏈韌性面臨全新考驗",
            "category": headline_art.get("category", "科技與AI"),
            "summary": headline_art.get("summary", "在技術快速迭代與資本高度集中的推動下，全球科技產業迎來全新分水嶺。市場一方面聚焦基礎建設投報率，另一方面也在密切評估技術外溢效應對整體生產力的長線提振。"),
            "key_points": [
                "先進製程與高頻寬記憶體需求持續超出預期",
                "主權 AI 與資料在地化法規重塑跨國技術部署格局",
                "企業端逐步由概念驗證 (PoC) 邁向規模化營運整合"
            ],
            "source": headline_art.get("source", "科技新報"),
            "url": headline_art.get("link", "https://technews.tw/")
        },
        "columns": cols,
        "stock_market": [
            {
                "title": "台積電先進封裝產能緊俏 帶動半導體供應鏈營運動能強勁",
                "market_tag": "台股焦點 • 權值龍頭",
                "summary": "晶圓代工龍頭持續擴產 CoWoS 與 2 奈米技術，帶動設備廠、材料商與封測族群買盤湧入，外資維持偏多加碼評等。",
                "trend_signal": "法人籌碼高度集中，留意相關供應鏈月營收年增率。",
                "source": "Yahoo 股市",
                "url": "https://tw.stock.yahoo.com/"
            },
            {
                "title": "美股 AI 巨頭資本支出上調 伺服器與高速傳輸概念股走揚",
                "market_tag": "美股動態 • 科技七巨頭",
                "summary": "微軟與亞馬遜等雲端巨頭維持高額 AI 基礎設施預算，帶動高頻寬記憶體與液冷散熱模組訂單能見度直達下半年度。",
                "trend_signal": "科技股那斯達克指數維持多頭架構，留意聯準會降息步伐。",
                "source": "Yahoo 股市",
                "url": "https://tw.stock.yahoo.com/"
            },
            {
                "title": "高股息 ETF 換股潮將屆 投信被動買盤聚焦穩健殖利率標的",
                "market_tag": "台股焦點 • ETF資金流",
                "summary": "多檔千億級高股息 ETF 進入成分股調整期，金融股與傳產績優高殖利率個股獲得顯著被動買盤支撐，成交量溫和放大。",
                "trend_signal": "內資投信連續買超，低本益比防禦型類股獲資金青睞。",
                "source": "中央社",
                "url": "https://feeds.feedburner.com/cnaFirstNews"
            }
        ],
        "sidebar": sidebars,
        "editorial": {
            "title": "在嘈雜的算法洪流中，尋找沉澱的文明錨點",
            "author": "晨報首席主筆 / Editorial Board",
            "commentary": "每日滾動的新聞標題往往充斥著市場的情緒與短期的焦慮。然而，當我們拉長時間軸審視，真正推動歷史齒輪的，從來不是單日幾百點的漲跌，而是底層技術架構的質變與制度規則的演進。在生成式智能鋪天蓋地的今日，人類社會最珍貴的資產依然是獨立思辨的定力與洞察本質的勇氣。看清週期，方能立於潮頭之上。",
            "quote": "「在資訊過剩的時代，清晰的思考就是最稀缺的權力。」"
        },
        "market_pulse": {
            "sentiment": "技術創新與結構轉型交織",
            "watch_topics": ["#AI代理生態", "#利率決議", "#半導體供應鏈", "#能源轉型"]
        }
    }


def load_env_file_if_present():
    """Lightweight loader for .env file without external dependencies."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(script_dir, ".env"),
        os.path.join(os.path.dirname(script_dir), ".env")
    ]
    for p in possible_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("\"'")
                            if k and not os.environ.get(k):
                                os.environ[k] = v
                break
            except Exception:
                pass

load_env_file_if_present()


def curate_newspaper_with_gemini(articles: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls Gemini API using google-genai SDK to curate a complete newspaper JSON.
    """
    gemini_cfg = config.get("gemini", {})
    # Priority: 1. Environment variable (or .env), 2. config.json "api_key"
    api_key = os.environ.get("GEMINI_API_KEY") or gemini_cfg.get("api_key")
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set (in env, .env, or config.json). Falling back to mock generator.")
        return create_mock_newspaper(articles, config)

    client = genai.Client(api_key=api_key)
    
    gemini_cfg = config.get("gemini", {})
    model_name = gemini_cfg.get("model", "gemini-2.5-flash")
    temperature = gemini_cfg.get("temperature", 0.3)
    focus_topics = config.get("focus_topics", [])
    max_arts = gemini_cfg.get("max_articles_to_analyze", 25)
    user_feedback = config.get("user_editorial_feedback", "")
    feedback_section = ""
    if user_feedback:
        feedback_section = f"\n【讀者/總編輯個人化偏好與審稿指令 (User Custom Directives)】：\n{user_feedback}\n請務必高度尊重並優先體現以上讀者回饋指令。\n"
    
    # Prepare articles for prompt
    selected_articles = articles[:max_arts]
    articles_text = ""
    for idx, art in enumerate(selected_articles, 1):
        articles_text += f"\n[{idx}] 來源: {art.get('source')} | 分類: {art.get('category')} | 標題: {art.get('title')}\n"
        articles_text += f"    時間: {art.get('published_at')} | 連結: {art.get('link')}\n"
        articles_text += f"    摘要: {art.get('summary')}\n"

    system_instruction = f"""
你是一位享譽全球的權威報社（如《金融時報》、《紐約時報》、《彭博社》）的「總編輯兼首席主筆」。
你的任務是審閱今日最新收集的各類新聞，為讀者策劃並排版一份極具深度、客觀嚴謹且排版層次分明的「每日晨間時報 (The Daily Times)」。
{feedback_section}
【每日四大優先涵蓋核心領域】：
一、台灣中央與地方政治、立法院與行政部門的重要制度變動、預算與法案、政黨重組、選舉制度及具公共政策影響的政治事件（原則上每天至少納入 1 至 3 則真正具有制度、政策或權力結構意義的政治新聞；若當日沒有足夠重要的政治發展，不勉強湊數）。
二、台灣與中國關係、中國政治、香港、東亞政局、區域安全與地緣政治。
三、全球民主政治、公民社會、威權擴張、各國大選與憲政發展。
四、AI 治理與 AI 能動性、數位身分與可驗證憑證、平台治理與內容審查、去中心化媒體與抗審查基礎設施、Web3、密碼龐克、新興科技政策、數位藝術與公共性。
五、股市與資本市場焦點：重大台股、美股與關鍵產業鏈之實質資本市場動態。

【嚴格排除原則】：
- 排除娛樂、體育、生活消費、純市場炒作、政壇花邊、單純口水攻防、缺乏公共意義的選舉馬聞、重複轉載及未經查核的政治指控。

【媒體來源多元性要求】：
- 嚴禁大量引用單一來源（例如不得全部來自單一入口網站），必須均衡涵蓋中央社、BBC中文、iThome、TechCrunch、CoinDesk、TechNews、各大財經與國際媒體。

【編輯與排版欄位準則】：
1. 【頭條焦點 (Headline)】：挑選今天最重大、具備高度制度或地緣影響的新聞作為大版面頭條。需提煉出震撼有力的主標題、副標題、流暢事實摘要，以及 3 個核心關鍵點 (key_points)。若具有市場或大宗商品連動，請一併提供 market_linkage。
2. 【重點新聞專欄 (Columns)】：精選 4 到 5 則核心新聞，嚴格優先涵蓋台灣制度法案、地緣區域安全、全球民主憲政、AI治理與抗審查政策。每則提供精煉摘要與一行關鍵啟示 (key_takeaway)。
   ★【市場指標與 10 日走勢連鎖 (market_linkage)】：只要該篇新聞涉及「地緣局勢（如荷姆茲海峽/中東/台海）」、「大宗商品（如原油/天然氣/黃金）」、「總經利率/通膨」或「半導體供應鏈」，務必附帶 market_linkage，精準列出關聯指標名稱（如布蘭特原油 Brent Crude、十年期美債殖利率、費城半導體）、近 10 日走勢與漲跌幅、實體產業鏈連鎖效應，以及 deep_dive_query。
3. 【股市與資本市場焦點 (stock_market)】：精選 3 則關鍵的台股、美股或權值/熱門概念股行情動能新聞。每則包含：市場標籤 (market_tag)、事實摘要 (summary)、行情或資金流向信號 (trend_signal)、來源與 URL。
4. 【側欄速報 (Sidebar)】：精選 4 到 6 則簡短快訊，讓讀者迅速掌握世界脈動。
5. 【主筆冷眼/銳評 (Editorial)】：撰寫一段 250~400 字極具洞察力、批判思辨的專欄短文，融會貫通今日政經與科技脈絡，並附上一句經典金句 (quote)。
6. 【市場與局勢脈動 (Market Pulse)】：簡述今日全球整體氛圍與 3-4 個關鍵話題標籤。

【文字與查核風格】：
- 全文使用標準「台灣正體中文」與「台灣慣用語」。
- 在摘要中清楚區分已確認事實、當事人主張、媒體獨家與分析，必要時用簡短語句標示不確定性。
- 務必保留所提供新聞的真實連結與正確來源名稱，嚴禁捏造網址。
"""

    prompt = f"""
以下是今日收集到的最新即時新聞清單（共 {len(selected_articles)} 則）：
==================================================
{articles_text}
==================================================

請根據以上新聞內容，以總編輯身份產出今日報紙的完整 JSON 結構。
"""

    candidate_models = [
        model_name,
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash-001"
    ]
    # Deduplicate while preserving order
    models_to_try = list(dict.fromkeys(candidate_models))

    for m in models_to_try:
        try:
            logger.info(f"Invoking Gemini model [{m}] via google-genai SDK...")
            response = client.models.generate_content(
                model=m,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    response_mime_type="application/json",
                    response_schema=NEWSPAPER_SCHEMA,
                )
            )
            
            raw_text = response.text
            if not raw_text:
                raise ValueError("Empty response text from Gemini API")
                
            data = json.loads(raw_text)
            logger.info(f"Successfully received and parsed curated newspaper from Gemini ({m})!")
            return data
        except Exception as e:
            logger.warning(f"Model {m} failed: {e}. Trying next fallback...")

    logger.error("All Gemini model attempts failed. Falling back to Mock newspaper.")
    return create_mock_newspaper(articles, config)


if __name__ == "__main__":
    test_config = {
        "gemini": {"model": "gemini-2.5-flash", "temperature": 0.3},
        "focus_topics": ["科技", "總經", "政治"],
        "newspaper": {"name": "THE DAILY TIMES"}
    }
    sample_news = [
        {"title": "台積電先進製程擴產帶動設備供應鏈", "source": "中央社", "category": "科技", "link": "https://cna.com.tw", "summary": "台積電持續擴充 2 奈米與先進封裝產能。"}
    ]
    res = curate_newspaper_with_gemini(sample_news, test_config)
    print(json.dumps(res, ensure_ascii=False, indent=2))
