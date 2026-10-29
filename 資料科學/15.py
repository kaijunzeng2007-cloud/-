
import os
import csv
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException
)

# ======================================
# 基本設定
# ======================================
KEYWORD = "xpath"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "xpath.csv")
DEBUG_FILE = os.path.join(BASE_DIR, "google_debug.html")

PROFILE = r"C:\selenium_xpath_profile"

MAX_PAGES = 10
WAIT_SECONDS = 25
MAX_SCROLLS = 35

driver = None
results = []
seen = set()

os.makedirs(PROFILE, exist_ok=True)

# ======================================
# Chrome 設定
# ======================================
options = webdriver.ChromeOptions()

options.add_argument("--start-maximized")
options.add_argument("--lang=zh-TW")
options.add_argument(f"--user-data-dir={PROFILE}")

# 隱藏自動化提示列（不保證所有版本有效）
options.add_experimental_option(
    "excludeSwitches", ["enable-automation"]
)

options.add_experimental_option(
    "useAutomationExtension", False
)

# ======================================
# 清理文字
# ======================================
def clean(text):
    return " ".join((text or "").split()).strip()


# ======================================
# 儲存 CSV
# ======================================
def save_csv():
    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["標題", "網址"]
        )

        writer.writeheader()
        writer.writerows(results)


# ======================================
# 儲存除錯 HTML
# ======================================
def save_debug():
    try:
        with open(
            DEBUG_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(driver.page_source)

        print("除錯檔案：", DEBUG_FILE)

    except WebDriverException:
        pass


# ======================================
# Google 驗證檢查
# ======================================
def is_verification():
    try:
        if "/sorry/" in driver.current_url.lower():
            return True

        body = driver.find_element(
            By.TAG_NAME, "body"
        ).text.lower()

        keywords = [
            "unusual traffic",
            "confirm you're not a robot",
            "recaptcha",
            "異常流量",
            "確認你不是機器人",
            "我不是機器人"
        ]

        return any(k in body for k in keywords)

    except WebDriverException:
        return False


def wait_verification():
    if not is_verification():
        return True

    print("\nGoogle 要求驗證，請在 Chrome 完成。")

    try:
        WebDriverWait(
            driver,
            180,
            poll_frequency=2
        ).until(
            lambda d: not is_verification()
        )

        print("驗證完成，自動繼續。")
        return True

    except TimeoutException:
        print("驗證逾時。")
        return False


# ======================================
# 等待搜尋結果
# ======================================
def has_results():
    try:
        return len(
            driver.find_elements(By.CSS_SELECTOR, "h3")
        ) > 0

    except WebDriverException:
        return False


def wait_results():
    try:
        WebDriverWait(
            driver,
            WAIT_SECONDS
        ).until(
            lambda d: has_results() or is_verification()
        )

    except TimeoutException:
        pass

    if is_verification():
        if not wait_verification():
            return False

        try:
            WebDriverWait(
                driver,
                WAIT_SECONDS
            ).until(lambda d: has_results())
        except TimeoutException:
            return False

    return has_results()


# ======================================
# 擷取所有 h3 標題與網址
# ======================================
def extract_results(page):
    count = 0

    data = driver.execute_script("""
        const output = [];

        document.querySelectorAll("h3").forEach(h3 => {
            const title = (
                h3.innerText ||
                h3.textContent ||
                ""
            ).trim();

            if (!title) return;

            // 優先尋找包住 h3 的超連結
            let link = h3.closest("a[href]");

            // 備援：從父層向上尋找
            if (!link) {
                let parent = h3.parentElement;

                for (let i = 0; i < 5 && parent; i++) {
                    if (
                        parent.tagName === "A" &&
                        parent.href
                    ) {
                        link = parent;
                        break;
                    }

                    parent = parent.parentElement;
                }
            }

            output.push({
                title: title,
                url: link ? link.href : ""
            });
        });

        return output;
    """)

    for item in data:
        title = clean(item.get("title"))
        url = (item.get("url") or "").strip()

        if not title:
            continue

        # 同一標題與網址只存一次
        key = (title, url)

        if key in seen:
            continue

        seen.add(key)

        results.append({
            "標題": title,
            "網址": url
        })

        count += 1

        print(f"\n第 {len(results)} 筆")
        print("標題：", title)
        print("網址：", url)

    if count:
        save_csv()

    return count


# ======================================
# 自動捲動並擷取
# ======================================
def scroll_and_extract(page):
    total = 0
    unchanged = 0
    previous_height = -1

    for _ in range(MAX_SCROLLS):

        if not wait_verification():
            return total, False

        total += extract_results(page)

        driver.execute_script(
            "window.scrollBy(0, 700);"
        )

        time.sleep(1)

        height = driver.execute_script(
            "return document.documentElement.scrollHeight;"
        )

        at_bottom = driver.execute_script("""
            return (
                window.scrollY + window.innerHeight
                >= document.documentElement.scrollHeight - 30
            );
        """)

        if at_bottom and height == previous_height:
            unchanged += 1
        else:
            unchanged = 0

        if unchanged >= 3:
            break

        previous_height = height

    total += extract_results(page)

    return total, True


# ======================================
# 頁面辨識
# ======================================
def page_signature():
    try:
        return driver.execute_script("""
            return Array.from(
                document.querySelectorAll("h3")
            ).slice(0, 5)
             .map(e => e.innerText)
             .join("|");
        """)

    except WebDriverException:
        return ""


# ======================================
# 點擊更多結果 / 下一頁
# ======================================
def click_more():
    old_url = driver.current_url
    old_signature = page_signature()

    selectors = [
        (By.ID, "pnnext"),
        (By.CSS_SELECTOR, "a[rel='next']"),
        (By.XPATH, "//a[contains(., '更多結果')]"),
        (By.XPATH, "//button[contains(., '更多結果')]"),
        (By.XPATH, "//a[contains(., '下一頁')]"),
        (By.XPATH, "//button[contains(., '下一頁')]"),
        (By.XPATH, "//a[contains(@aria-label, 'Next')]"),
        (
            By.XPATH,
            "//*[@role='button' and contains(., '更多結果')]"
        )
    ]

    for by, selector in selectors:
        buttons = driver.find_elements(by, selector)

        for button in buttons:
            try:
                if not button.is_displayed():
                    continue

                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    button
                )

                time.sleep(0.5)
                button.click()

                try:
                    WebDriverWait(
                        driver,
                        WAIT_SECONDS
                    ).until(
                        lambda d:
                        d.current_url != old_url
                        or page_signature() != old_signature
                        or is_verification()
                    )

                except TimeoutException:
                    pass

                if not wait_verification():
                    return False

                if (
                    driver.current_url != old_url
                    or page_signature() != old_signature
                ):
                    return True

            except (
                WebDriverException,
                StaleElementReferenceException
            ):
                continue

    return False


# ======================================
# Google 自動搜尋
# ======================================
def search_google():

    driver.get("https://www.google.com/?hl=zh-TW")

    if not wait_verification():
        return False

    try:
        search_box = WebDriverWait(
            driver,
            WAIT_SECONDS
        ).until(
            lambda d: d.find_element(By.NAME, "q")
        )

    except TimeoutException:
        print("找不到 Google 搜尋欄。")
        save_debug()
        return False

    search_box.click()
    search_box.clear()
    search_box.send_keys(KEYWORD)
    search_box.send_keys(Keys.ENTER)

    print(f"搜尋關鍵字：{KEYWORD}")

    try:
        WebDriverWait(
            driver,
            WAIT_SECONDS
        ).until(
            lambda d:
            "/search" in d.current_url
            or is_verification()
        )

    except TimeoutException:
        print("搜尋未成功。")
        save_debug()
        return False

    if not wait_verification():
        return False

    if not wait_results():
        print("搜尋結果未載入。")
        save_debug()
        return False

    return True


# ======================================
# 主程式
# ======================================
try:
    # 覆蓋舊 CSV
    save_csv()

    driver = webdriver.Chrome(options=options)

    if search_google():

        processed = set()

        for page in range(1, MAX_PAGES + 1):

            if not wait_verification():
                break

            if not wait_results():
                print("搜尋結果載入失敗。")
                save_debug()
                break

            signature = (
                driver.current_url,
                page_signature()
            )

            if signature in processed:
                print("偵測到重複頁面。")
                break

            processed.add(signature)

            print("\n" + "=" * 50)
            print(f"第 {page} 頁搜尋結果")
            print("=" * 50)

            count, completed = scroll_and_extract(page)

            print(f"\n本頁新增：{count} 筆")
            print(f"累計結果：{len(results)} 筆")

            save_csv()

            if not completed:
                break

            if count == 0:
                save_debug()

            if page >= MAX_PAGES:
                break

            if not click_more():
                print("\n沒有更多結果。")
                break

            time.sleep(2)

except Exception as e:
    print(f"\n錯誤：{type(e).__name__}: {e}")

    if driver is not None:
        save_debug()

finally:
    save_csv()

    if driver is not None:
        try:
            driver.quit()
        except WebDriverException:
            pass

    print("\n" + "=" * 50)
    print(f"搜尋關鍵字：{KEYWORD}")
    print(f"有效搜尋結果：{len(results)} 筆")
    print(f"CSV 位置：{CSV_FILE}")
    print("Chrome 已關閉")
    print("=" * 50)
