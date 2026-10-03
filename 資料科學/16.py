import csv
import time
from pathlib import Path
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


CSV_PATH = Path(__file__).resolve().parent / "agoda_result.csv"

# 用飯店名稱當 key，避免重複寫入
hotels = {}

driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 30)
stage = "開啟 Agoda"


def is_visible(element):
    try:
        return element.is_displayed()
    except Exception:
        return False


def click_lodging_tab():
    """明確選住宿，避免沿用到活動體驗模式。"""
    matches = driver.find_elements(
        By.XPATH,
        "//*[normalize-space()='住宿']"
    )

    for element in matches:
        if not is_visible(element):
            continue

        # 找到可點擊的父層；若找不到就點文字本身
        target = driver.execute_script("""
            let el = arguments[0];
            while (el && el !== document.body) {
                if (el.matches(
                    'button, [role="tab"], [role="button"], a, [tabindex]'
                )) {
                    return el;
                }
                el = el.parentElement;
            }
            return arguments[0];
        """, element)

        try:
            target.click()
        except Exception:
            driver.execute_script("arguments[0].click();", target)

        time.sleep(1)
        print("已點選住宿模式")
        return True

    return False


def choose_taichung_city(destination_input):
    """選台中市整座城市，排除市中心、行政區等地區建議。"""
    selectors = [
        '[role="option"]',
        '[data-selenium*="autocomplete"]',
        '[class*="autocomplete"]',
        '[class*="Autocomplete"]',
        "li",
    ]

    candidates = []
    seen = set()

    for selector in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            if not is_visible(element):
                continue

            text = " ".join(element.text.split())
            if not text or text in seen:
                continue
            seen.add(text)

            # 排除「位於台中市市中心」及各行政區等地區選項
            if "台中市" not in text:
                continue
            if any(word in text for word in [
                "市中心", "地區", "西屯", "北區", "中區",
                "南區", "東區", "逢甲", "區，"
            ]):
                continue

            candidates.append((len(text), element, text))

    # 較短的候選通常是單一建議項目，避免點到包含整個下拉清單的外層
    candidates.sort(key=lambda item: item[0])

    for _, element, text in candidates:
        try:
            target = driver.execute_script("""
                let el = arguments[0];
                while (el && el !== document.body) {
                    if (el.matches(
                        '[role="option"], button, li, [tabindex]'
                    )) {
                        return el;
                    }
                    el = el.parentElement;
                }
                return arguments[0];
            """, element)

            print("選取城市建議：", text)
            try:
                target.click()
            except Exception:
                driver.execute_script("arguments[0].click();", target)

            return True
        except Exception:
            continue

    # 找不到候選時列出畫面上的建議，避免不小心選到地區
    print("找不到可確認為整座城市的建議。畫面上的相關建議：")
    for selector in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            if is_visible(element) and "台中" in element.text:
                print("-", " ".join(element.text.split()))

    return False


def find_hotel_cards():
    selectors = [
        ".ssr-search-result-item",
        '[data-selenium="hotel-item"]',
        '[data-element-name="property-card"]',
        '[data-testid*="property"]',
        "[data-hotelid]",
    ]

    found = []
    seen_ids = set()

    for selector in selectors:
        for card in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if card.id not in seen_ids:
                    seen_ids.add(card.id)
                    found.append(card)
            except Exception:
                pass

        if found:
            return found

    return []


def extract_price_from_card(card):
    price_selectors = [
        ".hotel-price-container .soft-red",
        ".hotel-price-container .price",
        '[data-selenium="display-price"]',
        '[data-selenium*="price"]',
    ]

    for selector in price_selectors:
        for element in card.find_elements(By.CSS_SELECTOR, selector):
            text = " ".join(element.text.split())
            if text:
                return text

    return ""


def collect_visible_hotels():
    for card in find_hotel_cards():
        try:
            visible = driver.execute_script("""
                const rect = arguments[0].getBoundingClientRect();
                return rect.bottom > 0 && rect.top < window.innerHeight;
            """, card)

            if not visible:
                continue

            name_selectors = [
                ".hotel-name",
                '[data-selenium="hotel-name"]',
                "h3",
                "h4",
            ]

            name = ""
            for selector in name_selectors:
                elements = card.find_elements(By.CSS_SELECTOR, selector)
                name = next(
                    (element.text.strip() for element in elements
                     if element.text.strip()),
                    ""
                )
                if name:
                    break

            price = extract_price_from_card(card)

            if name and price:
                hotels[name] = [name, price]

        except Exception:
            # 頁面滾動時卡片可能重新載入，略過該張再繼續
            continue


def save_csv():
    rows = list(hotels.values())

    try:
        with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["飯店名稱", "特價"])
            writer.writerows(rows)
        print(f"CSV 位置：{CSV_PATH}")

    except PermissionError:
        # 常見原因是 CSV 正在 Excel 中開啟
        fallback_path = CSV_PATH.with_name(
            f"agoda_result_{datetime.now():%Y%m%d_%H%M%S}.csv"
        )
        with open(fallback_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["飯店名稱", "特價"])
            writer.writerows(rows)
        print("原 CSV 無法覆寫，可能正開在 Excel 中。")
        print(f"改存至：{fallback_path}")


try:
    stage = "開啟 Agoda"
    driver.get("https://www.agoda.com/zh-tw/")

    # 先明確切到住宿模式
    stage = "切換住宿模式"
    if not click_lodging_tab():
        print("找不到「住宿」分頁，先確認目前頁面上的住宿模式。")

    # 輸入台中
    stage = "輸入台中"
    destination = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'input[data-selenium="textInput"]')
        )
    )
    destination.click()
    destination.send_keys(Keys.CONTROL, "a")
    destination.send_keys("台中")

    # 選整座台中市，不選市中心或行政區
    stage = "選擇台中市"
    WebDriverWait(driver, 10).until(
        lambda d: any(
            element.is_displayed() and "台中" in element.text
            for element in d.find_elements(
                By.CSS_SELECTOR,
                '[role="option"], li, [class*="autocomplete"], '
                '[class*="Autocomplete"]'
            )
        )
    )

    if not choose_taichung_city(destination):
        raise RuntimeError(
            "沒有找到可確認為整座台中市的建議，已停止以免選到行政區。"
        )

    # 搜尋住宿
    stage = "搜尋住宿"
    search_button = wait.until(
        lambda d: d.execute_script("""
            const elements = [
                ...document.querySelectorAll(
                    'button, [role="button"], input[type="submit"]'
                )
            ];
            return elements.find(element =>
                element.getClientRects().length > 0 &&
                (element.innerText || element.value || '').trim() === '搜出好價'
            ) || null;
        """)
    )
    search_button.click()

    # 先辨認是不是又被導到活動搜尋，再等住宿卡片
    stage = "等待住宿結果列表"
    wait.until(
        lambda d:
            "/activities/" in d.current_url
            or len(find_hotel_cards()) > 0
            or "間住宿" in d.find_element(By.TAG_NAME, "body").text
    )

    if "/activities/" in driver.current_url:
        raise RuntimeError(
            "仍進入活動搜尋頁。請確認住宿分頁有被選取，且搜尋按鈕屬於住宿表單。"
        )

    print("住宿結果網址：", driver.current_url)

    # 模擬滑鼠滾動；新卡片連續多次沒有增加才停止
    stage = "滾動並擷取飯店資料"
    no_new_rounds = 0

    for turn in range(80):
        old_count = len(hotels)
        collect_visible_hotels()

        ActionChains(driver).scroll_by_amount(0, 650).perform()
        time.sleep(1.5)

        collect_visible_hotels()
        added = len(hotels) - old_count

        print(f"滾動 {turn + 1} 次：新增 {added} 間，累計 {len(hotels)} 間")

        if added == 0:
            no_new_rounds += 1
        else:
            no_new_rounds = 0

        if no_new_rounds >= 6:
            print("連續多次沒有新飯店，停止滾動。")
            break

except TimeoutException:
    print(f"程式停在「{stage}」：等待網頁元素逾時。")
    print("目前網址：", driver.current_url)

except Exception as error:
    print(f"程式停在「{stage}」時發生錯誤：{error}")
    print("目前網址：", driver.current_url)

finally:
    save_csv()
    print(f"飯店資料筆數：{len(hotels)}")

    try:
        driver.quit()
    except Exception:
        pass