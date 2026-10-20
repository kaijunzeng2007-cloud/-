
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# 設定搜尋關鍵字
KEYWORD = "科技"
PROFILE = r"C:\selenium_google_news_profile"

NEWS_URL = (
    f"https://news.google.com/search?q={KEYWORD}"
    "&hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
)


def clean_titles(titles):
    """清除空白與重複標題"""
    result = []

    for title in titles:
        title = " ".join(title.split()).strip()

        if title and title not in result:
            result.append(title)

    return result


def wait_for_verification(driver):
    """檢查 Google 是否要求驗證"""
    source = driver.page_source.lower()

    if any(k in source for k in [
        "captcha",
        "recaptcha",
        "i'm not a robot",
        "unusual traffic"
    ]):
        print("Google 可能要求機器人驗證")
        input("請完成驗證後按 Enter 繼續...")


def main():

    os.makedirs(PROFILE, exist_ok=True)

    # Chrome 設定
    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE}")
    options.add_argument("--lang=zh-TW")
    options.add_argument("--start-maximized")

    prefs = {
        "profile.managed_default_content_settings.images": 1
    }

    options.add_experimental_option("prefs", prefs)

    driver = None
    all_titles = []

    try:
        # 啟動 Chrome
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()

        # 開啟 Google 新聞
        driver.get(NEWS_URL)

        # 進入網頁後先停頓 3 秒
        time.sleep(3)

        # 檢查是否需要驗證
        wait_for_verification(driver)

        # 直接捲動到網頁最下面
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )

        # 到達底部後停頓 1 秒
        time.sleep(1)

        # 抓取新聞標題
        h3_elements = driver.find_elements(
            By.TAG_NAME, "h3"
        )

        for elem in h3_elements:
            all_titles.append(elem.text)

        # 若標題數量不足，使用超連結補充
        if len(all_titles) < 10:

            links = driver.find_elements(
                By.TAG_NAME, "a"
            )

            for link in links:
                text = link.text.strip()

                if len(text) > 10:
                    all_titles.append(text)

    except Exception as e:
        print(f"執行發生錯誤：{e}")

    finally:
        # 抓取完成後立即關閉 Chrome
        if driver:
            driver.quit()

    # 資料清洗
    cleaned_all = clean_titles(all_titles)

    # 分類新聞
    total_count = len(cleaned_all)

    if total_count >= 4:

        chunk = total_count // 4

        focus_news = cleaned_all[:chunk]
        local_news = cleaned_all[chunk:chunk*2]
        topic_news = cleaned_all[chunk*2:chunk*3]
        more_news = cleaned_all[chunk*3:]

    else:

        focus_news = cleaned_all
        local_news = []
        topic_news = []
        more_news = []

    # 顯示新聞結果
    print("\n" + "=" * 50)

    print(f"焦點新聞 ({len(focus_news)} 筆)：")
    for title in focus_news:
        print(f"  - {title}")

    print(f"\n地方新聞 ({len(local_news)} 筆)：")
    for title in local_news:
        print(f"  - {title}")

    print(f"\n您的主題 ({KEYWORD}) ({len(topic_news)} 筆)：")
    for title in topic_news:
        print(f"  - {title}")

    print(f"\n更多新聞 ({len(more_news)} 筆)：")
    for title in more_news:
        print(f"  - {title}")

    print("\n" + "=" * 50)
    print(f"總共取得 {total_count} 筆新聞標題")


if __name__ == "__main__":
    main()
