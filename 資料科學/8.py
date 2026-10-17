
import re  # 正規表示式，用來尋找上映日期
import time  # 控制網頁等待時間
import pandas as pd  # 整理資料並輸出 CSV
from bs4 import BeautifulSoup  # 解析 HTML
from urllib.parse import urljoin  # 補齊電影連結
from selenium import webdriver  # 自動操作瀏覽器
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# 老師指定的開眼電影網
URL = "https://www.atmovies.com.tw/movie/"

# 設定 Chrome 瀏覽器
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

# 啟動 Chrome
driver = webdriver.Chrome(options=options)

# 建立空字典，避免電影重複
movies = {}

# 日期格式，例如 2026/10/23
date_pattern = re.compile(
    r"20\d{2}/\d{1,2}/\d{1,2}"
)


# 清理多餘空白
def clean_text(text):
    return re.sub(
        r"\s+", " ", str(text or "")
    ).strip()


# 取得電影資料
def get_movies(html):

    # 使用 BeautifulSoup 解析網頁
    soup = BeautifulSoup(
        html, "html.parser"
    )

    # 尋找「近期上映強片」標題
    heading = soup.find(
        string=lambda text:
        text is not None
        and clean_text(text) == "近期上映強片"
    )

    if heading is None:
        print("找不到近期上映強片區塊")
        return

    # 從標題向上尋找輪播容器
    parent = heading.parent
    section = None

    for i in range(7):
        if parent is None:
            break

        # 檢查這個區塊有多少電影日期
        dates = date_pattern.findall(
            parent.get_text(" ", strip=True)
        )

        # 至少包含兩個日期，視為候選區塊
        if len(dates) >= 2:
            section = parent
            break

        parent = parent.parent

    if section is None:
        print("找不到電影輪播內容")
        return

    # 逐一搜尋輪播區塊中的連結
    for a in section.find_all("a", href=True):

        href = a.get("href", "")

        # 排除無效連結
        if not href or href == "#":
            continue

        if href.lower().startswith("javascript:"):
            continue

        # 補齊電影網址
        full_url = urljoin(URL, href)

        # 只保留電影介紹頁面
        if not re.search(
            r"/movie/[a-zA-Z0-9_-]+/?$",
            full_url
        ):
            continue

        # 取得連結內的文字
        text = clean_text(
            a.get_text(" ", strip=True)
        )

        # 有些電影日期在父元素中
        parent_text = clean_text(
            a.parent.get_text(" ", strip=True)
        )

        # 合併文字方便尋找日期
        combined = text + " " + parent_text

        # 尋找上映日期
        match = date_pattern.search(combined)

        if not match:
            continue

        release_date = match.group(0)

        # 優先使用連結本身的文字作為電影名稱
        title = date_pattern.sub("", text)
        title = clean_text(title)

        # 如果連結文字沒有名稱，使用父元素
        if not title:
            title = date_pattern.sub(
                "", parent_text
            )
            title = clean_text(title)

        # 排除無效電影名稱
        if not title or title.lower() == "more":
            continue

        # 使用網址當作唯一識別
        # 避免輪播複製元素造成重複
        movies[full_url] = {
            "電影名稱": title,
            "上映時間": release_date,
            "連結網址": full_url
        }


try:
    print("正在開啟開眼電影網...")

    # Selenium 開啟指定網址
    driver.get(URL)

    # 等待網頁載入
    WebDriverWait(driver, 20).until(
        lambda d: "近期上映強片"
        in d.page_source
    )

    time.sleep(3)

    # 先抓取網頁中已載入的電影
    get_movies(driver.page_source)

    print("正在抓取輪播電影...")

    # 尋找近期上映強片區塊的箭頭
    # 不同版本網站可能使用不同 class
    for i in range(20):

        # 取得目前網頁
        soup = BeautifulSoup(
            driver.page_source,
            "html.parser"
        )

        heading = soup.find(
            string=lambda text:
            text is not None
            and clean_text(text) == "近期上映強片"
        )

        if heading is None:
            break

        # 使用 Selenium 找輪播控制按鈕
        arrows = driver.find_elements(
            By.CSS_SELECTOR,
            ".slick-next, .swiper-button-next, "
            ".owl-next, .bx-next, "
            "a.next, button.next"
        )

        clicked = False

        for arrow in arrows:
            try:
                if arrow.is_displayed():
                    driver.execute_script(
                        "arguments[0].click();",
                        arrow
                    )
                    clicked = True
                    break
            except Exception:
                continue

        # 找不到可用箭頭就停止
        if not clicked:
            break

        time.sleep(0.8)

        # 每次切換後再次抓取
        get_movies(driver.page_source)

    # 建立 pandas 表格
    df = pd.DataFrame(
        list(movies.values()),
        columns=[
            "電影名稱",
            "上映時間",
            "連結網址"
        ]
    )

    # 沒有資料就顯示提醒
    if df.empty:
        print("沒有抓到電影，請檢查網頁結構")

    else:
        # 儲存 CSV
        df.to_csv(
            "movies.csv",
            index=False,
            encoding="utf-8-sig"
        )

        # 顯示抓取結果
        print("\n近期上映強片：")
        print(df.to_string(index=False))

        print(
            f"\n成功抓取 {len(df)} 部電影"
        )

        print("已輸出 movies.csv")

except Exception as error:
    print("程式發生錯誤：", error)

finally:
    # 關閉 Chrome 瀏覽器
    driver.quit()
