
import os
import csv
import time
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
# 基本設定
# ======================================
# 修改此處可更換搜尋主題；輸出檔名需另外修改 CSV_FILE。
KEYWORD = "xpath"
# 以程式所在資料夾為基準，避免執行位置影響檔案儲存位置。
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 結果 CSV 的輸出位置，欄位為「標題」與「網址」。
CSV_FILE = os.path.join(BASE_DIR, "xpath.csv")
# 發生載入問題時，儲存頁面 HTML 供檢查。
DEBUG_FILE = os.path.join(BASE_DIR, "google_debug.html")

# 專用 Chrome 資料夾，保留 Cookie 與工作階段；避免同時由多個程式使用。
PROFILE = r"C:\selenium_xpath_profile"

# 最多處理幾頁；沒有下一頁時會提早結束。
MAX_PAGES = 10
# 每輪頁面等待的上限（秒），不包含手動驗證時間。
WAIT_SECONDS = 25
# 每頁最多捲動幾次，避免動態頁面無限載入。
MAX_SCROLLS = 35
GOOGLE_HOSTS = {"google.com", "www.google.com", "google.com.tw", "www.google.com.tw"}

# 瀏覽器控制物件，尚未建立時為 None。
driver = None
# 依順序累積所有頁面收錄的結果。
results = []
# 記錄已收錄的原始網址，避免跨頁重複加入。
seen = set()


# ======================================
# Chrome 設定
# ======================================
options = webdriver.ChromeOptions()

# 沿用 a.py 已測試可用的部分自動化訊號設定；不保證免除網站驗證。
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")
# DOM 就緒後先返回，動態搜尋結果另外等待。
options.page_load_strategy = "eager"
options.add_experimental_option(
    "prefs", {"intl.accept_languages": "zh-TW,zh,en-US,en"}
)
options.add_argument("--lang=zh-TW")
# 沿用專用 Profile，保留上次瀏覽器工作階段的資料。
options.add_argument(f"--user-data-dir={PROFILE}")

# 隱藏自動化提示列（不保證所有版本有效）
options.add_experimental_option(
    "excludeSwitches", ["enable-automation"]
)



# ======================================
# 清理文字
# ======================================
# 清理換行與連續空白，讓每筆標題保持單行。
def clean(text):
    return " ".join((text or "").split()).strip()


# ======================================
# 儲存 CSV
# ======================================
# 寫入目前累積的全部結果；無資料時保留舊檔。
def save_csv():
    # 搜尋失敗或尚無資料時，不清空上次的 CSV。
    if not results:
        return False
    # 先寫入暫存檔，全部成功後再取代正式 CSV。
    temp_file = CSV_FILE + ".tmp"
    try:
        # BOM 協助 Excel 辨識中文；newline 避免額外空白列。
        with open(temp_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["標題", "網址"])
            writer.writeheader()
            writer.writerows(results)
        # 每次成功存檔都以目前累積結果更新正式檔案。
        os.replace(temp_file, CSV_FILE)
        return True
    finally:
        # 無論成功或失敗，都清理這次寫入留下的暫存檔。
        if os.path.exists(temp_file):
            os.remove(temp_file)


# ======================================
# 儲存除錯 HTML
# ======================================
# 儲存目前 DOM 的 HTML 快照，不會重新要求 Google 載入頁面。
def save_debug():
    try:
        with open(
            DEBUG_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(driver.page_source)

        print("除錯檔案：", DEBUG_FILE)

    except (WebDriverException, OSError):
        pass


# ======================================
# Google 驗證檢查
# ======================================
def is_verification():
    # 用網域、驗證頁路徑與可見元件辨識，避免搜尋結果文字造成誤判。
    parsed = urlparse(driver.current_url)
    if parsed.hostname not in GOOGLE_HOSTS:
        return False
    # 異常流量頁即使沒有驗證方塊，也能由 /sorry 路徑辨識。
    if parsed.path == "/sorry" or parsed.path.startswith("/sorry/"):
        return True
    return any(element.is_displayed() for element in driver.find_elements(
        By.CSS_SELECTOR,
        'iframe[src*="/recaptcha/"], .g-recaptcha, form[action*="/sorry/"]'
    ))


class VerificationCancelled(Exception):
    """使用者取消手動驗證。"""


class VerificationRequired(Exception):
    """從頁面等待切換至手動驗證。"""


def wait_verification():
    # 保留目前頁面，不刷新或重送搜尋，讓使用者手動完成驗證。
    while is_verification():
        print("\nGoogle 要求驗證，自動操作已暫停。")
        try:
            answer = input("請在 Chrome 完成驗證，跳轉後按 Enter 繼續；輸入 q 停止：")
        # 終端無法讀取輸入或使用者按 Ctrl+C 時，通知主程式停止。
        except (EOFError, KeyboardInterrupt):
            raise VerificationCancelled()
        # 輸入 q 取消；其他輸入則重新檢查驗證狀態。
        if answer.strip().lower() == "q":
            raise VerificationCancelled()
        try:
            WebDriverWait(driver, WAIT_SECONDS).until(
                lambda d: d.execute_script("return document.readyState")
                in ("interactive", "complete")
            )
        except TimeoutException:
            print("頁面尚未穩定，請確認驗證狀態。")
    return True


def wait_for_page(condition):
    # 每次驗證完成後，重新等待真正的目標元素；導頁時舊元素失效會重新尋找。
    # 每次輪詢先檢查是否需要驗證，再檢查呼叫端傳入的目標條件。
    def probe(d):
        if is_verification():
            raise VerificationRequired()
        return condition(d)

    while True:
        try:
            return WebDriverWait(
                driver, WAIT_SECONDS,
                # 導頁造成舊元素失效時，下一輪重新尋找元素。
                ignored_exceptions=(StaleElementReferenceException,)
            ).until(probe)
        except VerificationRequired:
            wait_verification()


# ======================================
# 等待搜尋結果
# ======================================
# 同時檢查搜尋網址與可見的結果標題，避免資料尚未出現就開始擷取。
def has_results():
    parsed = urlparse(driver.current_url)
    return (parsed.hostname in GOOGLE_HOSTS and parsed.path == "/search"
            and any(element.is_displayed() for element in driver.find_elements(
                By.CSS_SELECTOR, "#search a[href] h3"
            )))


# 等待結果就緒；逾時回傳 False，取消驗證則交由主程式處理。
def wait_results():
    try:
        wait_for_page(lambda d: has_results())
        return True
    except TimeoutException:
        return False


# ======================================
# 擷取所有 h3 標題與網址
# ======================================
# 一次取得搜尋區標題與連結，再清理、過濾及依網址去重。
def extract_results(page):
    count = 0

    data = driver.execute_script("""
        const output = [];

        document.querySelectorAll("#search a[href] h3").forEach(h3 => {
            const title = (
                h3.innerText ||
                h3.textContent ||
                ""
            ).trim();

            if (!title || !h3.getClientRects().length) return;

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

        # 忽略空白、非網頁連結，以及搜尋導覽用的 Google 內部網址。
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            continue
        if parsed.hostname in GOOGLE_HOSTS and parsed.path.startswith(
            ("/search", "/sorry", "/preferences")
        ):
            continue
        # 同一網址即使標題改變也只收錄一次。
        key = url

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

    # 本輪有新資料就立即保存，減少中途停止時的資料損失。
    if count:
        save_csv()

    return count


# ======================================
# 自動捲動並擷取
# ======================================
# 捲動當頁並累積新結果，回傳（新增筆數, 是否完成本頁）。
def scroll_and_extract(page):
    total = 0
    unchanged = 0
    # 同時比較頁面高度與累積筆數，避免只看高度就過早停止。
    previous_state = None

    for _ in range(MAX_SCROLLS):

        if not wait_results():
            return total, False

        total += extract_results(page)

        driver.execute_script(
            "window.scrollBy(0, 700);"
        )

        # 留時間讓捲動後的動態內容載入，再檢查頁面高度。
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

        # 位於頁底且頁高、筆數連續三輪不變，就視為本頁擷取完成。
        if unchanged >= 3:
            return total, True

        previous_state = state

    if wait_results():
        total += extract_results(page)
    # 達到捲動上限不等於完成本頁，因此不繼續翻頁。
    print("達到捲動上限，停止翻頁；已收錄的資料仍會儲存。")
    return total, False


# ======================================
# 頁面辨識
# ======================================
# 以前五個搜尋標題組成摘要，輔助偵測頁面變化，並非唯一識別碼。
def page_signature():
    try:
        return driver.execute_script("""
            return Array.from(
                document.querySelectorAll("#search a[href] h3")
            ).slice(0, 5)
             .map(e => e.innerText)
             .join("|");
        """)

    except WebDriverException:
        return ""


# ======================================
# 點擊更多結果 / 下一頁
# ======================================
# 尋找下一頁或更多結果按鈕，點擊後確認是否觀察到頁面變動。
def click_more():
    # 記住點擊前的網址與標題摘要，用於判斷頁面是否改變。
    old_url = driver.current_url
    old_signature = page_signature()

    # 依序嘗試 ID、CSS 與 XPath，以支援不同形式的翻頁控制項。
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

                # 先讓按鈕捲入視窗的位置穩定，再執行一般點擊。
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
# 開啟首頁、輸入關鍵字，完成必要驗證後等待搜尋結果。
def search_google():

    driver.get("https://www.google.com/?hl=zh-TW")

    if not wait_verification():
        return False

    try:
        search_box = wait_for_page(lambda d: next((
            box for box in d.find_elements(By.NAME, "q")
            if box.is_displayed() and box.is_enabled()
        ), False))

    except TimeoutException:
        print("找不到 Google 搜尋欄。")
        save_debug()
        return False

    search_box.click()
    # 清空預填文字，避免和這次關鍵字串在一起。
    search_box.clear()
    search_box.send_keys(KEYWORD)
    # 用 Enter 送出搜尋，再等待導頁與結果載入。
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
# 整合瀏覽器啟動、逐頁擷取、存檔與資源清理。
def main():
    global driver
    # 重新執行 main 時清空記憶體內資料，此處不會清空磁碟上的 CSV。
    results.clear()
    seen.clear()
    driver = None
    try:
        os.makedirs(PROFILE, exist_ok=True)
        driver = webdriver.Chrome(options=options)
        # 啟動參數之外再要求最大化，避免還原為舊視窗大小。
        driver.maximize_window()
        # 導航載入上限為 40 秒，與搜尋元素的等待時間分開計算。
        driver.set_page_load_timeout(40)

        if search_google():

            # 以網址與標題摘要記錄已處理頁面，避免翻頁失敗時重複擷取。
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

                # count 是本頁新增筆數；completed 表示是否到達穩定頁底。
                count, completed = scroll_and_extract(page)

                print(f"\n本頁新增：{count} 筆")
                print(f"累計結果：{len(results)} 筆")

                save_csv()

                if not completed:
                    break

                if count == 0:
                    save_debug()

                # 已達頁數上限時，不再多點一次下一頁。
                if page >= MAX_PAGES:
                    break

                if not click_more():
                    print("\n沒有更多結果。")
                    break

                # 翻頁後稍作等待，下一輪仍會確認搜尋結果真正載入。
                time.sleep(2)

    except VerificationCancelled:
        print("\n已取消驗證，停止後續請求。")

    except KeyboardInterrupt:
        print("\n使用者中止執行。")

    except Exception as e:
        print(f"\n錯誤：{type(e).__name__}: {e}")

        if driver is not None:
            save_debug()

    finally:
        # 不論正常結束、取消或發生錯誤，都再嘗試保存已收錄資料。
        saved = False
        try:
            saved = save_csv()
        except OSError as e:
            print(f"CSV 儲存失敗：{e}")

        if driver is not None:
            try:
                # 關閉這個 WebDriver 工作階段的所有 Chrome 視窗並釋放資源。
                driver.quit()
            except WebDriverException:
                pass

        print("\n" + "=" * 50)
        print(f"搜尋關鍵字：{KEYWORD}")
        print(f"有效搜尋結果：{len(results)} 筆")
        if saved:
            print(f"CSV 位置：{CSV_FILE}")
        else:
            print("本次未更新 CSV。")
        print("=" * 50)

# 直接執行本檔才啟動搜尋，被其他程式匯入時不會自動開啟 Chrome。
if __name__ == "__main__":
    main()
