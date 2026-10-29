# Python 網路爬蟲與自動化專案集錦
本專案集結多個使用 Python 進行網頁爬蟲、資料擷取與瀏覽器自動化的實戰程式碼。涵蓋的工具與技術包含 `Selenium`、`BeautifulSoup`、`Requests`、`Pandas` 以及 `Openpyxl`，應用範圍包含新聞、電影票房、電商商品、球員薪資與旅遊訂房等。
---
## 📁 檔案清單與功能總結
### 1. 電影與娛樂資訊

* **`1.py`：開眼電影網列表爬蟲**
* **技術**：`requests`, `BeautifulSoup`, `urllib.parse`
* **功能**：爬取開眼電影網新單元或電影列表，抓取電影標題、詳細內容、片長與網址。

* **`5.py`：台北週末票房 Excel 產出工具**
* **技術**：`Selenium`, `BeautifulSoup`, `Openpyxl`, `re`
* **功能**：自動翻頁抓取台北週末票房前 20 名電影，並利用 `openpyxl` 產出具有自定義樣式、千分位數字格式與自動篩選功能的 `Taipei_movies.xlsx`。

* **`8.py`：近期上映強片輪播爬蟲**
* **技術**：`Selenium`, `BeautifulSoup`, `re`
* **功能**：模擬點擊網頁輪播按鈕（Next），抓取開眼電影網「近期上映強片」的上映時間與電影名稱，去除重複後匯出 `movies.csv`。

### 2. 金融與公開資料

* **`2.py`：臺灣銀行牌告匯率爬蟲**
* **技術**：`Selenium`, `BeautifulSoup`, `Pandas`
* **功能**：抓取臺灣銀行最新牌告匯率，整理各幣別的現金與即期買賣匯率，並產出 `bank.csv`。

* **`3.py`：疾管署腸病毒統計資料下載器**
* **技術**：`requests`, `os`
* **功能**：直接透過 API 連結下載健保門診及住院就診人次統計（腸病毒）的 CSV 備份檔案。

### 3. 電商與商品爬蟲

* **`4.py`：博客來關鍵字書籍爬蟲**
* **技術**：`Selenium`, `BeautifulSoup`, `csv`
* **功能**：在博客來搜尋指定關鍵字（如「演算法」），抓取書名、作者、價格與商品網址，並產出 `booklist.csv`。

* **`11.py`（原檔名 `10.py`）：分頁式電商商品爬蟲**
* **技術**：`Selenium`, `csv`
* **功能**：爬取分頁式商品網頁（NBA 範例網站），自動點擊「下一頁」，將每一頁的商品編號、名稱與價格分別儲存為獨立的 `NBA_Products{page}.csv`。

* **`12.py`：Google 搜尋結果爬蟲（Steam 遊戲推薦）**
* **技術**：`Selenium`, `csv`
* **功能**：以「Steam 遊戲推薦」為關鍵字進行 Google 自動搜尋，捲動頁面抓取第一頁的 H3 標題與網址，並支援 Google 機器人驗證等待機制，最後產出 `steam_game_recommendations_.csv`。

* **`13.py`：Momo 購物網自動搜尋測試**
* **技術**：`Selenium`
* **功能**：自動開啟 Momo 購物網、於搜尋框輸入關鍵字「nba」並按下 Enter，最後將搜尋結果的網頁原始碼存成 `NBA_test.html`。

* **`15.py`：進階多頁 Google 搜尋 XPath 爬蟲**
* **技術**：`Selenium`, `csv`
* **功能**：進階版 Google 搜尋爬蟲，支援多頁自動翻頁、除錯 HTML 儲存、驗證攔截與即時存檔，產出 `xpath.csv`。

* **`16.py`：Agoda 台中飯店即時價格爬蟲**
* **技術**：`Selenium`, `csv`, `ActionChains`
* **功能**：自動操作 Agoda 網站，鎖定台中地區並模擬點擊城市建議與搜尋，切換至結果分頁後自動滾動頁面，擷取飯店名稱與特價並儲存至 `agoda_result.csv`。

### 4. 體育與社群論壇

* **`6.py`：Basketball Reference 球員名單爬蟲**
* **技術**：`Selenium`, `BeautifulSoup`, `csv`
* **功能**：抓取指定 NBA 球隊（CLE、HOU、GSW）2024 年球員名單中的背號、位置、體重、生日等 8 個欄位，並產出 `players.csv`。

* **`10.py`（原檔名 `9.py`）：PTT 八卦版 18 歲驗證繞過爬蟲**

* **技術**：`Selenium`
* **功能**：透過寫入 Cookie (`over18=1`) 繞過 PTT 的 18 歲年齡確認畫面，直接進入八卦版抓取文章標題、網址與作者。
* **`14.py`：HoopsHype 球員薪資與詳細資料爬蟲**

* **技術**：`Selenium`, `BeautifulSoup`, `Pandas`, `requests`
* **功能**：抓取 HoopsHype 全聯盟球員薪資表格（自動展開全部筆數），輸出 `all_play.csv`；並進一步抓取前 3 名高薪球員的個人頁面，擷取球員背號後輸出 `highest.csv`。

### 5. 新聞與其他自動化

* **`9.py`（原檔名 `8.py`：Google 新聞分類爬蟲**
* **技術**：`Selenium`
* **功能**：結合 Chrome 使用者設定檔（Profile）維持登入狀態，抓取 Google 新聞指定關鍵字（如「科技」）的標題，進行資料清洗並自動分類（焦點、地方、主題、更多新聞）。

* **`17.py`：GitHub 登入與動態頁面擷取**
* **技術**：`Selenium`
* **功能**：自動登入 GitHub 帳號，等待動態載入完成後擷取左側欄與中央動態區的文字內容。
---
## ⚙️ 環境安裝與需求
在執行這些 Python 程式之前，請確保您的環境已安裝 Python 3.8+ 以及下列必要的第三方套件：
```bash
pip install requests beautifulsoup4 selenium pandas openpyxl webdriver-manager
```
* **瀏覽器需求**：多數腳本使用 `Selenium` 執行，請確保電腦中已安裝 **Google Chrome** 瀏覽器（部分腳本支援 Edge）。
* **ChromeDriver**：若使用較新版本的 Selenium，通常會自動管理驅動程式；若遇版本不相容，可搭配 `webdriver-manager` 進行自動更新。
