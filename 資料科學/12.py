
import os
import re
import csv
import time
import traceback
from urllib.parse import quote

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

KEYWORD = "Steam 遊戲推薦"
PROFILE = r"C:\selenium_google_news_profile"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "steam_game_recommendations_.csv")

URL = (
    "https://www.google.com/search?q="
    + quote(KEYWORD)
    + "&hl=zh-TW&gl=TW"
)


def get_results(driver):
    results = []
    seen = set()

    for heading in driver.find_elements(By.CSS_SELECTOR, "h3"):
        title = heading.text.strip()

        try:
            href = heading.find_element(
                By.XPATH, "./ancestor::a[1]"
            ).get_attribute("href")
        except Exception:
            continue

        if not title or not href or href in seen:
            continue

        seen.add(href)
        results.append([title, href])

    return results


def delete_old_csv():
    pattern = re.compile(
        r"steam_game_recommendations(?:_\d+)?\.csv"
    )

    for filename in os.listdir(BASE_DIR):
        if pattern.fullmatch(filename):
            os.remove(os.path.join(BASE_DIR, filename))


def main():
    driver = None

    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--user-data-dir=" + PROFILE)

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        driver.get(URL)

        results = []
        verification_shown = False

        # 最多等待 90 秒，不重複發送搜尋請求
        deadline = time.monotonic() + 90

        while time.monotonic() < deadline:
            current_url = driver.current_url

            if "/sorry/" in current_url:
                if not verification_shown:
                    print("Google 要求驗證。")
                    print("請在 Chrome 視窗完成驗證，不用回 VS Code 按 Enter。")
                    verification_shown = True
            else:
                results = get_results(driver)

                if results:
                    break

            time.sleep(2)

        if not results:
            print("未取得搜尋結果，程式已停止。")
            print("目前網址：", driver.current_url)
            print("原本的 CSV 不會被刪除或覆蓋。")
            return

        print("搜尋關鍵字：", KEYWORD)
        print("有效搜尋結果：", len(results))

        for i, (title, href) in enumerate(results, 1):
            print(f"\n第 {i} 筆")
            print("標題：", title)
            print("網址：", href)

        # 先成功儲存新檔案，再刪除舊的編號檔案
        temp_path = CSV_PATH + ".tmp"

        with open(
            temp_path, "w", newline="", encoding="utf-8-sig"
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["搜尋標題", "網址"])
            writer.writerows(results)

        os.replace(temp_path, CSV_PATH)
        delete_old_csv()

        print("\nCSV 儲存成功：", CSV_PATH)

    except Exception:
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
