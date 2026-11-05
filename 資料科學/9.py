
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# 設定搜尋關鍵字
KEYWORD = "科技"
# 固定使用者資料目錄可保留瀏覽器設定與 Cookie，供下次執行使用。
PROFILE = r"C:\selenium_google_news_profile"

# hl 指定介面語言、gl 指定地區、ceid 指定台灣繁體中文新聞版本。
NEWS_URL = (
    f"https://news.google.com/search?q={KEYWORD}"
    "&hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
)


def clean_titles(titles):
    """清除空白與重複標題"""
    result = []

    for title in titles:
        # 將換行與連續空白合併成一個空格，方便比較標題。
        title = " ".join(title.split()).strip()

        # 略過空標題與重複標題，並保留原本出現的順序。
        if title and title not in result:
            result.append(title)

    return result


def wait_for_verification(driver):
    """檢查 Google 是否要求驗證"""
    # 轉成小寫後檢查驗證相關字樣；這是簡易判斷，可能出現誤判。
    source = driver.page_source.lower()

    if any(k in source for k in [
        "captcha",
        "recaptcha",
        "i'm not a robot",
        "unusual traffic"
    ]):
        print("Google 可能要求機器人驗證")
        # 暫停程式，讓使用者在瀏覽器完成驗證後手動繼續。
        input("請完成驗證後按 Enter 繼續...")


def main():

    # 資料夾已存在時不報錯，首次執行則自動建立。
    os.makedirs(PROFILE, exist_ok=True)

    # Chrome 設定
    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE}")
    options.add_argument("--lang=zh-TW")
    options.add_argument("--start-maximized")

    # 圖片設定值 1 代表允許載入圖片。
    prefs = {
        "profile.managed_default_content_settings.images": 1
    }

    options.add_experimental_option("prefs", prefs)

    # 先設為 None，讓瀏覽器啟動失敗時，finally 仍可安全檢查。
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
        # 先嘗試以 h3 標籤取得標題，實際結果取決於網站當時的 HTML 結構。
        h3_elements = driver.find_elements(
            By.TAG_NAME, "h3"
        )

        for elem in h3_elements:
            all_titles.append(elem.text)

        # 若標題數量不足，使用超連結補充
        # 此處依清洗前的數量判斷；補抓的長連結文字也可能包含非新聞內容。
        if len(all_titles) < 10:

            links = driver.find_elements(
                By.TAG_NAME, "a"
            )

            for link in links:
                text = link.text.strip()

                if len(text) > 10:
                    all_titles.append(text)

    # 顯示執行錯誤；已取得的標題仍會在關閉瀏覽器後進行整理。
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

    # 依取得順序平均切成四組，並非依新聞內容或網站實際分類判斷。
    if total_count >= 4:

        # 整數除法取得每組基本筆數；無法整除的剩餘標題放入最後一組。
        chunk = total_count // 4

        focus_news = cleaned_all[:chunk]
        local_news = cleaned_all[chunk:chunk*2]
        topic_news = cleaned_all[chunk*2:chunk*3]
        more_news = cleaned_all[chunk*3:]

    else:

        # 少於四筆時，全部列入焦點新聞，其餘三組保持空白。
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


# 只有直接執行此檔案時才啟動主程式；被其他模組匯入時不會自動執行。
if __name__ == "__main__":
    main()
