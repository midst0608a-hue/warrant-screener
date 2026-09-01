# 📰 每日新聞報紙生成器 (Daily Automated Newspaper Generator)

透過 Python 抓取最新熱門新聞 RSS，結合 Google 官方最新 `google-genai` SDK（Gemini 2.5 Flash / Pro）進行智慧總編輯策展，每日定時產出具備古典/現代報紙排版（Broadsheet & The Mesh Times 風格）的精美靜態網頁與 PDF 報紙。

---

## ✨ 核心特色

1. **多來源新聞即時擷取 (`fetcher.py`)**：
   - 支援各大優質新聞 RSS（財經總經、科技前沿、國際局勢、Web3 等）。
   - 自動時區轉換與 24 小時時間窗口精準過濾，清洗雜質 HTML。

2. **Gemini 2.5 總編輯智慧策展 (`summarizer.py`)**：
   - 採用最新 `google-genai` SDK 與嚴格 JSON 結構約束。
   - 自動評選**大版面頭條焦點 (Headline)**、**重點新聞專欄 (Columns)**、**全球速報 (Sidebar Briefs)**。
   - 撰寫犀利深度的**主筆冷眼/銳評專欄 (Editorial)** 與每日金句。
   - 內建離線/防爆備援機制，無 API Key 亦可流暢預覽。

3. **典雅報紙前端排版 (`template.html` + `render.py`)**：
   - **古典報頭與標題**：雙層黑線、卷期號碼、格言、出版天數自動推算。
   - **CSS Grid 多欄佈局**：大版面 3 欄式設計、首字下沉（Drop Caps）、專欄格線。
   - **主題切換**：內建「📜 復古羊皮紙」、「☀️ 現代白報紙」、「🌙 沉浸夜讀」三種主題。
   - **轉存與列印**：內建 `@media print` 專屬樣式，一鍵列印或轉存高清 PDF 報紙。

4. **一鍵本地運行與 GitHub Actions 雲端自動發布**：
   - Windows 雙擊 `generate_daily.bat` 即可生成並自動開啟瀏覽器。
   - 附帶 GitHub Actions 工作流，每天清晨定時自動編排並發布至 GitHub Pages。

---

## 📁 專案架構

```
daily_newspaper/
├── config.json               # 系統設定檔（RSS來源、Gemini模型、關注主題、報頭名稱）
├── fetcher.py                # 資訊收集模組（RSS抓取、時間篩選、文字清洗）
├── summarizer.py             # 智慧處理模組（Gemini 2.5 API 調用、結構化策展）
├── template.html             # 報紙前端模板（CSS Grid、古典字體、首字下沉）
├── render.py                 # 渲染引擎（Jinja2 注入資料並生成靜態 HTML）
├── main.py                   # 主程式入口（一鍵串接完整工作流）
├── generate_daily.bat        # Windows 本地一鍵執行腳本
├── requirements.txt          # Python 依賴清單
├── .github/workflows/        # 自動化排程
│   └── daily_newspaper.yml  # GitHub Actions 定時執行與 Pages 自動部署
└── README.md                 # 說明文件
```

---

## 🚀 快速開始

### 1. 安裝環境與依賴

建議使用 Python 3.9 以上環境：

```bash
cd daily_newspaper
pip install -r requirements.txt
```

### 2. 設定 Gemini API Key

請前往 [Google AI Studio](https://aistudio.google.com/) 取得免費 API Key：

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY="您的_GEMINI_API_KEY"
```

**Windows CMD:**
```cmd
set GEMINI_API_KEY=您的_GEMINI_API_KEY
```

**Linux / macOS:**
```bash
export GEMINI_API_KEY="您的_GEMINI_API_KEY"
```

*(註：若未設定 `GEMINI_API_KEY`，系統會自動切換為 Mock 示範模式進行排版預覽)*

### 3. 一鍵生成報紙

**本地執行：**
```bash
python main.py
```
執行完成後，系統會生成 `newspaper.html` 並自動在您的預設瀏覽器中開啟預覽！

**Windows 使用者捷徑：**
直接滑鼠雙擊 `generate_daily.bat` 即可。

---

## ⚙️ 常用指令參數

```bash
# 使用離線 Mock 模式快速測試前端排版（不消耗 API Token）
python main.py --mock

# 指定自訂輸出檔案名稱
python main.py --output my_daily_edition.html

# 生成後不自動跳出瀏覽器（適合排程背景執行）
python main.py --no-open

# 儲存 Gemini 策展完成的中間 JSON 資料
python main.py --save-json
```

---

## 🌐 雲端自動化 (GitHub Actions + GitHub Pages)

本專案已備妥 GitHub Actions 自動化腳本，讓您免租用伺服器即可擁有自己的每日早報線上網站：

1. 將本專案推送至您的 GitHub 儲存庫。
2. 進入 GitHub 儲存庫的 **Settings > Secrets and variables > Actions**。
3. 新增一個 Repository Secret：
   - Name: `GEMINI_API_KEY`
   - Value: 您的 Google Gemini API Key
4. 進入 **Settings > Pages**，將 Source 設定為 **GitHub Actions**。
5. 每天台灣時間早上 06:30，GitHub Actions 將會自動抓取新聞、調用 Gemini 生成報紙，並自動部署至您的 GitHub Pages 網址！
