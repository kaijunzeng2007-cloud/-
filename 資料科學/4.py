
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
FOLDER = Path(__file__).resolve().parent
CSV_PATH = FOLDER / "booklist.csv"


# 清理文字
def clean(text):
    return " ".join(text.split()).strip()


# 抓取書籍資料
def get_books(html):
    soup = BeautifulSoup(html, "html.parser")
    books = []
    seen = set()

    # 每本書的 HTML 區塊
    cards = soup.select(
        'div.table-td[id^="prod-itemlist-"]'
    )

    for card in cards:

        # 1. 書名
        title_tag = card.select_one("h4 a[title]")

        if not title_tag:
            continue

        title = clean(title_tag.get("title", ""))

        # 2. 商品編號與網址
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
            name = clean(
                tag.get("title", "")
                or tag.get_text(strip=True)
            )

            if name and name not in authors:
                authors.append(name)

        author = "、".join(authors)

        # 4. 書價
        price_tags = card.select("ul.price li b")

        price = ""

        if price_tags:
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
        WebDriverWait(driver, 20).until(
            lambda d: d.find_elements(
                By.CSS_SELECTOR,
                'div.table-td[id^="prod-itemlist-"]'
            )
        )

    except TimeoutException:
        print("等待搜尋結果逾時")

    time.sleep(1)

    # 取得網頁原始碼
    html = driver.page_source

    # 解析書籍資料
    books = get_books(html)

finally:
    # 自動關閉 Chrome
    driver.quit()


# 儲存 CSV
if books:

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

        writer.writeheader()
        writer.writerows(books)

    # 統計空白資料
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
