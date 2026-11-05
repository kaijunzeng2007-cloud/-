
import csv
import time
from pathlib import Path
from urllib.parse import quote
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# 搜尋關鍵字
KEYWORD = "演算法"

# 博客來搜尋網址
URL = (
    "https://search.books.com.tw/search/query/key/"
    + quote(KEYWORD) + "/cat/all"
)

# CSV 儲存位置
# 以程式檔案所在目錄為基準，避免從不同工作目錄執行時改變輸出位置。
FOLDER = Path(__file__).resolve().parent
CSV_PATH = FOLDER / "booklist.csv"


# 清理文字
def clean(text):
    # split() 拆開各種空白（含換行、定位字元），再用單一空格接回文字。
    return " ".join(text.split()).strip()


# 抓取書籍資料
def get_books(html):
    soup = BeautifulSoup(html, "html.parser")
    books = []
    # 用集合記錄已處理的商品編號，避免同一商品重複加入。
    seen = set()

    # 每本書的 HTML 區塊
    # CSS 選擇器中的 ^= 表示 id 必須以指定文字開頭。
    cards = soup.select(
        'div.table-td[id^="prod-itemlist-"]'
    )

    for card in cards:

        # 1. 書名
        title_tag = card.select_one("h4 a[title]")

        # 略過沒有書名連結的區塊，避免後續讀取不存在的標籤。
        if not title_tag:
            continue

        title = clean(title_tag.get("title", ""))

        # 2. 商品編號與網址
        # 從區塊 id 去掉固定前綴，留下建立商品網址所需的編號。
        product_id = card.get("id", "").replace(
            "prod-itemlist-", "", 1
        )

        if not title or not product_id:
            continue

        if product_id in seen:
            continue

        seen.add(product_id)

        book_url = (
            "https://www.books.com.tw/products/"
            + product_id
        )

        # 3. 作者
        authors = []

        author_tags = card.select(
            'p.author a[rel="go_author"]'
        )

        for tag in author_tags:
            # 優先使用 title 屬性；若為空，再使用連結顯示文字。
            name = clean(
                tag.get("title", "")
                or tag.get_text(strip=True)
            )

            if name and name not in authors:
                authors.append(name)

        # 多位作者以頓號串接；沒有作者時保留空字串。
        author = "、".join(authors)

        # 4. 書價
        price_tags = card.select("ul.price li b")

        price = ""

        if price_tags:
            # 取最後一個粗體價格欄位，並移除千分位逗號；仍以字串儲存。
            price = clean(
                price_tags[-1].get_text()
            ).replace(",", "")

        # 加入書籍資料
        books.append({
            "書名": title,
            "網址": book_url,
            "作者": author,
            "書價": price
        })

    return books


# 啟動 Chrome
options = webdriver.ChromeOptions()

# 啟動時最大化瀏覽器
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)

# 確保 Chrome 視窗最大化
driver.maximize_window()

books = []

try:
    driver.get(URL)

    # 等待書籍載入
    try:
        # 最多等待 20 秒，找到至少一個商品區塊便繼續。
        WebDriverWait(driver, 20).until(
            lambda d: d.find_elements(
                By.CSS_SELECTOR,
                'div.table-td[id^="prod-itemlist-"]'
            )
        )

    except TimeoutException:
        print("等待搜尋結果逾時")

    # 再留 1 秒讓頁面內容補齊；即使前面逾時，仍會嘗試解析現有 HTML。
    time.sleep(1)

    # 取得網頁原始碼
    html = driver.page_source

    # 解析書籍資料
    books = get_books(html)

# 不論擷取成功或發生例外，都執行 finally 釋放瀏覽器資源。
finally:
    # 自動關閉 Chrome
    driver.quit()


# 儲存 CSV
if books:

    # newline="" 避免 CSV 出現多餘空白列；utf-8-sig 方便 Excel 辨識中文。
    with open(
        CSV_PATH,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "書名",
                "網址",
                "作者",
                "書價"
            ]
        )

        # 先寫欄位名稱，再依 fieldnames 的順序輸出每一本書的字典資料。
        writer.writeheader()
        writer.writerows(books)

    # 統計空白資料
    # 空字串經 not 判斷為 True；sum 會把每個 True 計為 1。
    missing_author = sum(
        not book["作者"] for book in books
    )

    missing_price = sum(
        not book["書價"] for book in books
    )

    print(f"成功抓取 {len(books)} 本書")
    print(f"作者空白：{missing_author} 筆")
    print(f"書價空白：{missing_price} 筆")
    print(f"已儲存：{CSV_PATH}")

else:
    print("無法取得書籍資料")
