# -
這是一份為你的專案量身打造的 `README.md` 文件。專案主要涵蓋了多個使用 **Python**、**Selenium**、**BeautifulSoup** 進行網頁爬蟲與資料科學處理的實作範例。

你可以直接複製以下內容並貼到你的 `README.md` 檔案中：

---

# 📊 Python 網路爬蟲與資料科學專案集

本專案收錄了多個 Python 網路爬蟲實作範例，主要運用 `Selenium`、`BeautifulSoup` 與 `Pandas` 等工具，實現自動化瀏覽、網頁解析、表格資料抓取以及資料清洗與匯出（CSV）。

---

## 🛠️ 技術堆疊 (Tech Stack)

* **程式語言**：Python
* **網頁解析**：BeautifulSoup4, Regular Expressions (`re`)
* **自動化測試/動態爬蟲**：Selenium WebDriver (`Chrome`, `Edge`)
* **資料處理與匯出**：Pandas
* **網路請求**：Requests, Urllib3

---

## 📂 專案檔案結構與功能說明

| 檔案名稱 | 核心功能與說明 | 主要使用技術 |
| --- | --- | --- |
| **`期中14.py`** | 爬取 HoopsHype 網站的 **NBA 球員薪資排行榜**，自動將表格展開為全部顯示或透過 JS 處理，並抓取前三名高薪球員的詳細資料，最終匯出 `all_play.csv` 與 `highest.csv`。

 | Selenium, BeautifulSoup, Pandas |
| **`1.py`** | 爬取 **開眼電影網** 的最新上映電影資訊，擷取電影標題、詳細內容、片長與頁面網址。

 | Requests, BeautifulSoup |
| **`2.py`** | 爬取 **臺灣銀行最新牌告匯率**，自動解析現金買入、現金賣出、即期買入與即期賣出等匯率資訊，並格式化輸出 `bank.csv`。

 | Selenium, BeautifulSoup, Pandas |
| **`3.py`** | 從政府資料開放平臺自動下載 **腸病毒健保就診統計 CSV 資料**，並具備 SSL 憑證異常時的容錯處理與 UTF-8 編碼優化。

 | Requests, Urllib3 |
| **`10.py`** | 自動處理 **PTT 網站** 的滿 18 歲年齡驗證 Cookie，成功進入八卦版並抓取首頁文章列表的標題、作者與網址。

 | Selenium |
| **`12.py`** | 針對 Google 搜尋引擎進行自動化關鍵字搜尋（如「Steam 遊戲推薦」），處理 Google 驗證防護機制，並將搜尋結果整理匯出為 CSV。

 | Selenium, Pandas |
| **`13.py`** | 自動開啟 **momo 購物網**，模擬使用者在搜尋框輸入關鍵字（如 `nba`）並送出，抓取搜尋結果頁面並存成 HTML 測試檔。 | Selenium |
| **`16.py`** | 自動化操作 **Agoda 訂房網**，模擬輸入「台中」並選取城市建議、設定搜尋條件，自動滾動頁面抓取多筆飯店名稱與特價資訊，匯出 `agoda_result.csv`。

 | Selenium, Pandas, ActionChains |
| **`17.py`** | 自動登入 **GitHub** 帳號，並在登入成功後抓取使用者左側欄與中央動態區（Feed）的頁面文字內容。

 | Selenium |

---

## 🚀 快速開始與環境安裝

1. **複製專案到本地端：**
```bash
git clone <你的專案網址>
cd <專案資料夾>

```


2. **安裝必要套件：**
確保你的環境已安裝 Python，並執行以下指令安裝相依套件：
```bash
pip install pandas beautifulsoup4 requests selenium webdriver-manager

```


3. **執行特定爬蟲腳本：**
以執行臺灣銀行匯率爬蟲為例：
```bash
python 2.py

```



---

## ⚠️ 注意事項

* 本專案中的 Selenium 腳本多數預設使用 **Google Chrome** 瀏覽器，請確保電腦已安裝 Chrome 瀏覽器，`webdriver-manager` 會自動幫您管理對應的 Driver 版本。
* 部分網站（如 Google、Agoda、PTT）具有反爬蟲機制或驗證碼保護，執行時若遇到安全驗證，請依照終端機提示手動完成驗證再繼續。
