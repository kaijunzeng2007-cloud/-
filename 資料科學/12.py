
import os
import csv
import time
import json
from urllib.parse import urlparse

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
# 1. 基本設定
# ======================================

# 想搜尋其他主題時，修改這個關鍵字即可。
KEYWORD = "Steam 遊戲推薦"

# 專用 Chrome 資料夾，保留 Cookie 與工作階段；勿同時由多個程式使用。
PROFILE = r"C:\selenium_steam_profile"

# 以程式所在資料夾為基準，避免執行位置不同導致輸出位置改變。
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CSV_FILE = os.path.join(
    BASE_DIR,
    "steam_game_recommendations.csv"
)

# 每輪頁面條件等待的上限（秒），不包含手動驗證的時間。
WAIT_SECONDS = 25
# 捲動次數上限，避免動態頁面無限執行。
MAX_SCROLLS = 35
# 控制部分自動化訊號設定，無法保證免除網站驗證。
HIDE_AUTOMATION_FLAGS = True
# True 會在終端列印瀏覽器環境資訊，供除錯使用。
DEBUG_BROWSER = False
# 允許辨識為 Google 搜尋頁或驗證頁的網域。
GOOGLE_HOSTS = {"google.com", "www.google.com", "google.com.tw", "www.google.com.tw"}

# 瀏覽器環境設定
LANGUAGE = "zh-TW"
TIMEZONE = "Asia/Taipei"

# 台中市的大致座標
# 只供需要地理位置授權的網站使用
LATITUDE = 24.1477
LONGITUDE = 120.6736


# ======================================
# 2. 清理文字
# ======================================

def clean(text):
    # 將換行、Tab 及連續空白合併成單一空白；None 視為空字串。
    return " ".join(
        (text or "").split()
    ).strip()


# ======================================
# 3. 建立 Chrome
# ======================================

def create_driver():
    # 建立專用 Chrome 工作階段，套用語言、視窗、時區及定位設定。

    os.makedirs(
        PROFILE,
        exist_ok=True
    )

    options = webdriver.ChromeOptions()

    if HIDE_AUTOMATION_FLAGS:
        # 只調整 Chrome 的部分自動化訊號，不代表能通過網站驗證。
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--disable-blink-features=AutomationControlled")

    # Chrome Profile
    options.add_argument(
        f"--user-data-dir={PROFILE}"
    )

    # Chrome 語言
    options.add_argument(
        f"--lang={LANGUAGE}"
    )

    # 啟動時最大化，配合目前螢幕的可用範圍。
    options.add_argument("--start-maximized")

    # 一般瀏覽器功能設定
    options.add_argument(
        "--disable-notifications"
    )

    options.add_argument(
        "--no-first-run"
    )

    options.add_argument(
        "--no-default-browser-check"
    )

    # 讓 HTTP Accept-Language 與語言設定一致
    options.add_experimental_option(
        "prefs",
        {
            "intl.accept_languages":
                "zh-TW,zh,en-US,en"
        }
    )

    # 不使用自訂假 User-Agent
    # 沿用 Chrome 自己的真實版本資訊

    # eager 在 DOM 就緒時返回；動態搜尋結果另外等待。
    options.page_load_strategy = "eager"

    driver = webdriver.Chrome(
        options=options
    )

    # 啟動後再次要求最大化，避免還原成之前的視窗大小。
    driver.maximize_window()

    # 導航最多等待 40 秒，與搜尋元素的等待上限分開計算。
    driver.set_page_load_timeout(40)

    # 設定台灣時區
    driver.execute_cdp_cmd(
        "Emulation.setTimezoneOverride",
        {
            "timezoneId": TIMEZONE
        }
    )

    # 設定網站定位 API 的座標；不會改變對外 IP 或自動授予定位權限。
    driver.execute_cdp_cmd(
        "Emulation.setGeolocationOverride",
        {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "accuracy": 100
        }
    )

    return driver


# ======================================
# 4. 瀏覽器指紋檢查
# ======================================

def inspect_browser(driver):
    # 讀取目前頁面可見的環境資訊，僅供診斷，不會修改這些屬性。

    info = driver.execute_script("""
        const canvas = document.createElement("canvas");

        let webgl = false;
        let webgpu = false;

        try {
            webgl = !!(
                canvas.getContext("webgl") ||
                canvas.getContext("experimental-webgl")
            );
        } catch (e) {
            webgl = false;
        }

        try {
            webgpu = !!navigator.gpu;
        } catch (e) {
            webgpu = false;
        }

        return {
            userAgent: navigator.userAgent,
            language: navigator.language,
            languages: navigator.languages,
            platform: navigator.platform,
            webdriver: navigator.webdriver,
            timezone: Intl.DateTimeFormat()
                .resolvedOptions().timeZone,
            screenWidth: screen.width,
            screenHeight: screen.height,
            innerWidth: window.innerWidth,
            innerHeight: window.innerHeight,
            cpuThreads: navigator.hardwareConcurrency,
            deviceMemory: navigator.deviceMemory ?? null,
            webRTC: !!(
                window.RTCPeerConnection ||
                window.webkitRTCPeerConnection
            ),
            webGL: webgl,
            webGPU: webgpu
        };
    """)

    print("\n瀏覽器環境檢查")
    print("=" * 50)

    print(
        json.dumps(
            info,
            ensure_ascii=False,
            indent=4
        )
    )

    print("=" * 50)

    return info


# ======================================
# 5. Google 驗證檢查
# ======================================

def is_verification(driver):
    parsed = urlparse(driver.current_url)
    hostname = (parsed.hostname or "").lower()
    if hostname not in GOOGLE_HOSTS:
        return False

    # 異常流量頁即使沒有驗證方塊，仍可由 /sorry 路徑辨識。
    if parsed.path == "/sorry" or parsed.path.startswith("/sorry/"):
        return True

    # 只判斷可見的驗證元件，避免搜尋結果提到 reCAPTCHA 就誤判。
    return any(
        element.is_displayed()
        for element in driver.find_elements(
            By.CSS_SELECTOR,
            'iframe[src*="/recaptcha/"], .g-recaptcha, '
            'form[action*="/sorry/"]'
        )
    )


def wait_for_verification(driver):
    """保留目前頁面，讓使用者手動驗證；不重整或重送搜尋。"""
    while is_verification(driver):
        print("\n偵測到 Google 驗證，已暫停自動操作。")
        try:
            answer = input(
                "請在 Chrome 手動完成驗證，頁面跳轉後按 Enter 繼續；輸入 q 停止："
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n已停止；驗證尚未完成。")
            return False
        if answer == "q":
            return False
        # 等待驗證後的導頁穩定；仍在驗證頁時繼續暫停。
        try:
            WebDriverWait(driver, WAIT_SECONDS).until(
                lambda d: d.execute_script("return document.readyState")
                in ("interactive", "complete")
            )
        except TimeoutException:
            print("頁面尚未穩定，請確認瀏覽器中的驗證狀態。")
    return True


# 使用者取消驗證時，通知主程式進入資料儲存與資源清理流程。
class VerificationCancelled(Exception):
    pass


# 在一般等待中發現驗證頁時，切換至手動驗證流程。
class VerificationRequired(Exception):
    pass


def wait_for_page(driver, condition):
    """每次手動驗證後重新等待目標元素，不以 URL 或 readyState 當完成。"""
    # 每次輪詢先確認沒有驗證，再檢查呼叫端傳入的頁面條件。
    def probe(d):
        if is_verification(d):
            raise VerificationRequired()
        return condition(d)

    while True:
        try:
            return WebDriverWait(
                driver, WAIT_SECONDS,
                # 導頁造成舊元素失效時，下一次輪詢會重新尋找元素。
                ignored_exceptions=(StaleElementReferenceException,)
            ).until(probe)
        except VerificationRequired:
            if not wait_for_verification(driver):
                raise VerificationCancelled()


def search_box_ready(driver):
    # 回傳可見且可輸入的搜尋欄；找不到時回傳 False，讓等待繼續。
    return next((box for box in driver.find_elements(By.NAME, "q")
                 if box.is_displayed() and box.is_enabled()), False)


def results_ready(driver):
    # 搜尋網址與可見的結果標題都就緒才繼續，避免資料尚未載入就開始擷取。
    parsed = urlparse(driver.current_url)
    return (
        parsed.hostname in GOOGLE_HOSTS and parsed.path == "/search"
        and any(item.is_displayed() for item in driver.find_elements(
            By.CSS_SELECTOR, "#search a[href] h3"
        ))
    )


# ======================================
# 6. 擷取 Google 搜尋結果
# ======================================

def extract_results(driver, results, seen):
    # 從搜尋區一次讀取標題與連結，清理後更新 results 清單與 seen 網址集合。

    data = driver.execute_script("""
        const output = [];

        document.querySelectorAll("#search a[href] h3").forEach(h3 => {

            const title = (
                h3.innerText ||
                h3.textContent ||
                ""
            ).trim();

            if (!title || !h3.getClientRects().length) return;

            const link = h3.closest("a[href]");

            if (!link || !link.href) return;

            output.push({
                title: title,
                url: link.href
            });

        });

        return output;
    """)

    for item in data:

        title = clean(
            item.get("title")
        )

        url = (
            item.get("url") or ""
        ).strip()

        if not title:
            continue

        if "AI 模式已回覆" in title:
            continue

        if not url.startswith(
            ("https://", "http://")
        ):
            continue

        # 排除部分 Google 內部網址
        parsed = urlparse(url)
        hostname = (
            parsed.hostname or ""
        ).lower()

        if hostname in (
            "google.com",
            "www.google.com"
        ):
            if parsed.path.startswith(
                ("/search", "/sorry", "/preferences")
            ):
                continue

        # 同一原始網址只收錄一次，即使標題不同也不重複加入。
        key = url

        if key in seen:
            continue

        seen.add(key)

        results.append({
            "標題": title,
            "網址": url
        })

        print(
            f"\n第 {len(results)} 筆"
        )

        print(
            f"標題：{title}"
        )

        print(
            f"網址：{url}"
        )


# ======================================
# 7. 第一頁自動捲動
# ======================================

def scroll_first_page(driver, results, seen):

    # 到達頁底後，頁高與筆數連續三輪不變，就視為本頁擷取完成。
    unchanged = 0
    previous_state = None

    for _ in range(MAX_SCROLLS):

        wait_for_page(driver, results_ready)

        extract_results(
            driver,
            results,
            seen
        )

        driver.execute_script(
            "window.scrollBy(0, 700);"
        )

        # 等待捲動後的動態內容載入，再判斷頁面高度。
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

        state = (height, len(results))
        if at_bottom and state == previous_state:
            unchanged += 1

        else:
            unchanged = 0

        if unchanged >= 3:
            return True

        previous_state = state

    if not wait_for_verification(driver):
        return False

    extract_results(
        driver,
        results,
        seen
    )

    # 達上限不代表已到頁底，回傳 False 讓主程式另存部分結果。
    print("已達捲動上限，結果標記為部分資料。")
    return False


# ======================================
# 8. 儲存 CSV
# ======================================

def save_csv(results, target=None):
    # 未指定目標時使用正式檔名；沒有資料時不覆寫既有檔案。
    target = target or CSV_FILE

    if not results:
        return False

    # 先寫暫存檔，全部成功後再取代目標，減少產生不完整 CSV 的機會。
    temp_file = target + ".tmp"

    try:

        with open(
            temp_file,
            "w",
            newline="",
            # 使用 BOM 協助 Excel 辨識中文；newline 避免多餘空白列。
            encoding="utf-8-sig"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "標題",
                    "網址"
                ]
            )

            writer.writeheader()
            writer.writerows(results)

        os.replace(
            temp_file,
            target
        )

        return True

    finally:

        # 不論成功或失敗，都清理這次寫入留下的暫存檔。
        if os.path.exists(temp_file):
            os.remove(temp_file)


# ======================================
# 9. 主程式
# ======================================

def main():

    driver = None

    results = []
    seen = set()

    # completed 表示本頁是否擷取完成；blocked 表示使用者取消驗證。
    completed = False
    blocked = False

    try:

        driver = create_driver()

        # 不再額外開啟測試網站；沿用原本的 Google 首頁搜尋方式。
        driver.get("https://www.google.com/?hl=zh-TW")
        if DEBUG_BROWSER:
            inspect_browser(driver)
        search_box = wait_for_page(driver, search_box_ready)

        # 輸入關鍵字
        search_box.click()
        search_box.clear()
        search_box.send_keys(KEYWORD)

        # 執行搜尋
        search_box.send_keys(Keys.ENTER)

        wait_for_page(driver, results_ready)

        print(
            f"\n搜尋關鍵字：{KEYWORD}"
        )

        print("=" * 50)

        completed = scroll_first_page(
            driver,
            results,
            seen
        )

    except VerificationCancelled:
        blocked = True

    except KeyboardInterrupt:
        print("\n使用者中止執行")

    except TimeoutException:
        print(
            "Google 搜尋結果載入逾時"
        )

    except WebDriverException as e:
        print(
            f"瀏覽器執行錯誤：{e}"
        )

    except Exception as e:
        print(
            f"執行錯誤：{e}"
        )

    finally:

        saved = False

        # 未完成時另存部分資料，保留上次完整結果的正式 CSV。
        output_file = CSV_FILE if completed else os.path.splitext(CSV_FILE)[0] + ".partial.csv"
        if results:

            try:
                saved = save_csv(results, output_file)

            except OSError as e:
                print(
                    f"CSV 儲存失敗：{e}"
                )

        if driver:

            try:
                # 關閉這個 WebDriver 工作階段的所有瀏覽器視窗。
                driver.quit()

            except WebDriverException:
                pass

        print("\n" + "=" * 50)

        print(
            f"搜尋關鍵字：{KEYWORD}"
        )

        print(
            f"第一頁搜尋結果：{len(results)} 筆"
        )

        if saved:

            print(
                f"CSV 已儲存：{output_file}"
            )

        else:

            print(
                "未更新 CSV，保留原有檔案"
            )

        if blocked:

            print(
                "驗證未完成或已取消，本次停止請求"
            )

        print("Chrome 已關閉")
        print("=" * 50)


# 直接執行本檔才啟動搜尋；被其他程式匯入時不會開啟 Chrome。
if __name__ == "__main__":
    main()
