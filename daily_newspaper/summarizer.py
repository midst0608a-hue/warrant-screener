"""
Gemini Intelligence & Editorial Module (Summarizer)
Uses google-genai SDK to analyze raw news articles and curate a structured newspaper edition.
"""

import os
import sys
import re
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


def _extract_sentences(text: str) -> List[str]:
    """Helper to split text into clean, well-formatted sentence segments."""
    if not text:
        return []
    # Strip common news wire prefix patterns like （中央社記者...電）
    cleaned_text = re.sub(r"^[（(][^）)]+(?:電|訊|報)[）)]\s*", "", text.strip())
    cleaned_text = re.sub(r"^\[[^\]]+\]\s*", "", cleaned_text)
    
    # Split by standard Chinese and English delimiters
    parts = re.split(r"[。！？；\n]+", cleaned_text)
    cleaned = []
    for p in parts:
        s = p.strip().strip("，、 ")
        if len(s) >= 8:
            if len(s) > 50:
                s = s[:48] + "..."
            cleaned.append(s)
    return cleaned


def _derive_takeaway(title: str, summary: str, category: str, index: int = 0) -> str:
    """Generate a unique, context-aware key takeaway based on article content."""
    combined = (title + " " + summary).lower()
    
    if any(k in combined for k in ["中東", "航空", "杜拜", "原油", "能源", "油價", "波斯灣", "海峽"]):
        options = [
            "留意地緣緊張局勢對國際客貨運航線、能源供應與全球物流成本之潛在衝擊。",
            "關注跨國航運避險路徑調整與原油供應鏈韌性之實質變化。",
            "區域突發變局左右能源定價，持續評估對航空與運輸產業獲利之影響。"
        ]
        return options[index % len(options)]
    elif any(k in combined for k in ["宣傳", "資訊戰", "認知戰", "假消息", "虛假", "俄羅斯", "烏克蘭", "情報", "駭客", "資安"]):
        options = [
            "社群網路與認知作戰交織，凸顯跨國事實查核與數位資訊防禦之重要性。",
            "威權體系跨國資訊操弄加劇，關注公民社會韌性與平台內容治理進展。",
            "留意新型態混合戰略對地緣政治互信與公眾輿論之深層干擾。"
        ]
        return options[index % len(options)]
    elif any(k in combined for k in ["外交", "帛琉", "盟友", "友邦", "兩岸", "中國", "中共", "國安", "軍", "地緣", "印太"]):
        options = [
            "關注印太區域地緣戰略博弈、防務安全與多邊外交實質進展。",
            "評估跨國盟友合作機制對區域經貿與地緣戰略穩定之長遠影響。",
            "留意區域安全形勢變動對國際航運與周邊供應鏈之連鎖效應。"
        ]
        return options[index % len(options)]
    elif any(k in combined for k in ["立法院", "行政院", "法案", "政策", "政黨", "預算", "憲政", "選舉", "政治", "陳其邁", "沈伯洋", "市長"]):
        options = [
            "評估制度法案修訂對公共治理架構與跨部會行政協調之長遠效應。",
            "關注重大公共政策推進節奏與社會各界民意權益之平衡溝通。",
            "地方治理實務考驗政治人物面對危機之承擔力與政策落實透明度。"
        ]
        return options[index % len(options)]
    elif any(k in combined for k in ["教會", "律師", "人權", "人身", "民主", "公民", "審查"]):
        options = [
            "關注公民社會韌性、司法法治與國際人道倡議之跨國連鎖迴響。",
            "威權體制擴張背景下，跨國庇護與人權法制機制備受國際重視。"
        ]
        return options[index % len(options)]
    elif any(k in combined for k in ["裁員", "車", "福斯", "關稅", "製造", "傳統產業", "競爭"]):
        options = [
            "跨國貿易壁壘與產業轉型夾擊下，製造巨頭加速重組以維持營運動能。",
            "觀察全球供應鏈重構過程中之成本控制、市占率洗牌與就業市場衝擊。"
        ]
        return options[index % len(options)]
    elif any(k in combined for k in ["債", "房", "房貸", "利率", "通膨", "降息", "央行", "聯準會", "貨幣"]):
        options = [
            "利率與信用環境波動下，密切關注資金流向、資產定價與融資成本變化。",
            "債券殖利率上行直接衝擊實體借貸需求，留意資產負債表承壓情況。",
            "持續追蹤各國央行政策路徑對實體經濟與資金流動性之引導效應。"
        ]
        return options[index % len(options)]
    elif any(k in combined for k in ["ai", "人工智慧", "半導體", "晶片", "科技", "算力", "模型", "台積電", "輝達"]):
        options = [
            "留意算力基建投資回報率與新興技術垂直落地之商用轉化效率。",
            "追蹤先進製程資本支出與關鍵設備材料供應鏈之動能消長。",
            "技術競爭焦點轉向性價比與領域專用微調，加速產業生態重塑。"
        ]
        return options[index % len(options)]
    elif any(k in combined for k in ["加密", "比特幣", "以太坊", "web3", "區塊鏈"]):
        options = [
            "留意鏈上流動性重分配與全球合規監管架構之演進脈絡。",
            "機構資金參與度提升，帶動去中心化基礎設施成熟度。"
        ]
        return options[index % len(options)]
    else:
        # Contextual fallback using article's title
        short_title = title[:14]
        return f"持續關注「{short_title}」後續事態發展與相關領域之實質效應。"


def create_mock_newspaper(articles: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback generator in case Gemini API key is missing or network is unavailable."""
    logger.warning("Using Dynamic Fallback Newspaper Generator...")
    sample_arts = articles if articles else []
    
    # 1. Headline Selection
    headline_art = sample_arts[0] if len(sample_arts) > 0 else {
        "title": "全球半導體與 AI 算力基礎設施迎來新一輪擴張潮",
        "link": "https://technews.tw/",
        "source": "科技新報",
        "category": "科技與AI",
        "summary": "各大科技巨頭近期持續加大先進製程與資料中心投資，推動相關供應鏈營運動能強勁。產業專家指出，隨著生成式應用逐步由概念驗證走向規模化落地，高頻寬記憶體與先進封裝產能將維持高度緊俏。"
    }
    
    # Dynamic Headline Subtitle & Key Points
    h_title = headline_art.get("title", "重大時政與產業前瞻報導")
    h_summary = headline_art.get("summary", "")
    h_cat = headline_art.get("category", "今日頭條焦點")
    
    # Extract key points from summary sentences
    sentences = _extract_sentences(h_summary)
    if len(sentences) >= 3:
        h_key_points = sentences[:3]
    elif len(sentences) == 2:
        h_key_points = [
            sentences[0],
            sentences[1],
            _derive_takeaway(h_title, h_summary, h_cat, 0)
        ]
    elif len(sentences) == 1:
        h_key_points = [
            sentences[0],
            f"關鍵脈絡：{h_title}",
            _derive_takeaway(h_title, h_summary, h_cat, 0)
        ]
    else:
        h_key_points = [
            f"事件核心：{h_title}",
            "各方利益與制度架構面臨深度重塑與調適",
            _derive_takeaway(h_title, h_summary, h_cat, 0)
        ]
    
    # Subtitle based on topic
    if "帛琉" in h_title or "外交" in h_title or "友邦" in h_title or "太平洋" in h_title:
        h_subtitle = "凝聚多邊戰略共識之際，印太區域和平與供應鏈韌性成焦點"
    elif "政治" in h_cat or "政策" in h_cat:
        h_subtitle = "重大法制制度推進之際，公共政策與各界權益面臨新平衡"
    elif "科技" in h_cat or "AI" in h_cat:
        h_subtitle = "前瞻技術加速演進之際，產業生態與算力架構迎來升級"
    elif "財經" in h_cat or "總經" in h_cat:
        h_subtitle = "全球金融情勢波動之際，市場資金流向與定價邏輯深度重構"
    else:
        h_subtitle = sentences[0] if sentences else "深度剖析重大事件脈絡與長遠制度影響"
    if len(h_subtitle) > 40:
        h_subtitle = h_subtitle[:38] + "..."

    # 2. Columns (Focus News)
    cols = []
    col_arts = sample_arts[1:6] if len(sample_arts) > 1 else []
    for i, a in enumerate(col_arts):
        c_title = a.get("title", f"重大市場動態報導第 {i+1} 則")
        c_summary = a.get("summary", "")
        c_cat = a.get("category", "重點新聞")
        takeaway = _derive_takeaway(c_title, c_summary, c_cat, i)
        
        cols.append({
            "title": c_title,
            "category": c_cat,
            "summary": c_summary[:130] + ("..." if len(c_summary) > 130 else ""),
            "key_takeaway": takeaway,
            "source": a.get("source", "權威報導"),
            "url": a.get("link", "#")
        })
        
    if not cols:
        cols = [
            {
                "title": "美歐通膨數據趨緩 降息路徑成為市場關注焦點",
                "category": "總經與財經",
                "summary": "全球主要經濟體通膨指標呈現漸進回落，市場對貨幣政策寬鬆週期的預期升溫，資金流向新興市場。",
                "key_takeaway": "實質利率下行有助於改善企業融資成本與流動性環境。",
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

    # 3. Stock Market Items (Search scraped articles for financial/market ones)
    stock_arts = []
    used_links = {headline_art.get("link", "")} | {c.get("url", "") for c in cols}
    
    for a in sample_arts:
        if a.get("link") in used_links:
            continue
        c_text = (a.get("title", "") + " " + a.get("summary", "")).lower()
        if any(k in c_text for k in ["股", "產經", "財經", "台積電", "營收", "外資", "法人", "美股", "etf", "市場", "資本", "關稅", "車", "減產"]):
            stock_arts.append(a)
            used_links.add(a.get("link"))
            if len(stock_arts) >= 3:
                break
                
    stock_market = []
    for i, a in enumerate(stock_arts):
        s_title = a.get("title", "")
        s_summary = a.get("summary", "")
        # Dynamic tag
        if "台" in s_title or "台積電" in s_title:
            stag = "台股焦點 • 權值動態"
        elif "美" in s_title or "關稅" in s_title:
            stag = "全球市場 • 跨國經貿"
        elif "車" in s_title or "製造" in s_title or "裁員" in s_title:
            stag = "產業脈動 • 結構轉型"
        else:
            stag = "資本市場 • 焦點快訊"
            
        stock_market.append({
            "title": s_title,
            "market_tag": stag,
            "summary": s_summary[:100] + ("..." if len(s_summary) > 100 else ""),
            "trend_signal": _derive_takeaway(s_title, s_summary, "財經", i + 3),
            "source": a.get("source", "財經快訊"),
            "url": a.get("link", "#")
        })
        
    if len(stock_market) < 3:
        default_stocks = [
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
                "trend_signal": "科技股維持多頭架構，留意聯準會利率決策步伐。",
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
        ]
        stock_market.extend(default_stocks[len(stock_market):3])

    # 4. Sidebar Items
    sidebars = []
    remaining_arts = [a for a in sample_arts if a.get("link") not in used_links]
    for i, a in enumerate(remaining_arts[:5]):
        sidebars.append({
            "title": a.get("title", f"全球速覽快訊 {i+1}"),
            "category": a.get("category", "國際簡訊"),
            "brief": a.get("summary", "全球主要區域政經局勢與產業最新進展速讀。")[:65] + "...",
            "source": a.get("source", "國際編譯"),
            "url": a.get("link", "#")
        })
    if not sidebars:
        sidebars = [
            {"title": "原油期貨窄幅震盪", "category": "大宗商品", "brief": "產油國減產協議與全球需求預測拉鋸，能源價格維持區間走勢。", "source": "鉅亨網", "url": "#"},
            {"title": "加密資產機構資金穩定流入", "category": "Web3", "brief": "現貨 ETF 交易量平穩，鏈上活躍地址數創近期新高。", "source": "BlockTempo", "url": "#"},
            {"title": "綠色能源供應鏈法規更新", "category": "國際局勢", "brief": "歐盟發布新版碳邊境機制細則，跨國製造業加緊低碳轉型。", "source": "BBC 中文", "url": "#"}
        ]

    # 5. Dynamic Editorial
    editorial_title = f"在變局中審視秩序：從「{h_title[:14]}」談起"
    editorial_commentary = (
        f"每日滾動的新聞標題往往充斥著即時的市場情緒與短期的焦慮。然而，當我們拉長時間軸審視「{h_title[:18]}」等重大發展，"
        f"真正推動歷史齒輪的，從來不是單日幾百點的漲跌或即時的政治口水，而是底層制度規則的演進、地緣政治的再平衡，以及關鍵產業技術架構的質變。"
        f"在資訊高度碎裂與算法洪流的今日，洞察本質與保持清醒思辨依然是面對未知週期最關鍵的定力。"
    )

    return {
        "headline": {
            "title": h_title,
            "subtitle": h_subtitle,
            "category": h_cat,
            "summary": h_summary if h_summary else "在國際與產業變局交織的推動下，相關體系迎來全新分水嶺。市場一方面聚焦實質制度進展，另一方面也在密切評估外溢效應對整體長線發展的提振。",
            "key_points": h_key_points,
            "source": headline_art.get("source", "焦點特稿"),
            "url": headline_art.get("link", "#")
        },
        "columns": cols,
        "stock_market": stock_market,
        "sidebar": sidebars,
        "editorial": {
            "title": editorial_title,
            "author": "晨報首席主筆 / Editorial Board",
            "commentary": editorial_commentary,
            "quote": "「在資訊過剩的時代，清晰的思考就是最稀缺的權力。」"
        },
        "market_pulse": {
            "sentiment": "地緣局勢與產業轉型交織博弈",
            "watch_topics": [f"#{h_cat}", "#地緣安全", "#政策制度", "#產業轉型", "#資本流向"]
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
