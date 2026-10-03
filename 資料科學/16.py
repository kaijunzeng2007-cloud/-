import csv
import re
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
hotels = {}

driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 30)
stage = "開啟 Agoda"


def find_first_city_suggestion(destination):
    """找輸入框下方最上方的台中建議項目。"""
    input_bottom = destination.rect["y"] + destination.rect["height"]
    candidates = []

    elements = driver.find_elements(
        By.XPATH, "//*[contains(normalize-space(.), '台中')]"
    )

    for element in elements:
        try:
            if not element.is_displayed():
                continue

            text = " ".join(element.text.split())
            if not text or len(text) > 80:
                continue

            rect = element.rect
            if rect["y"] < input_bottom - 5:
                continue

            candidates.append((rect["y"], len(text), element, text))
        except Exception:
            continue

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1]))

    for _, _, element, text in candidates:
        try:
            clickable = driver.execute_script("""
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

            return clickable, text
        except Exception:
            continue

    return None


def find_hotel_cards():
    selectors = [
        ".ssr-search-result-item",
        '[data-selenium="hotel-item"]',
        '[data-element-name="property-card"]',
        '[data-testid*="property"]',
        "[data-hotelid]",
    ]

    for selector in selectors:
        cards = driver.find_elements(By.CSS_SELECTOR, selector)
        if cards:
            return cards

    return []


def hotel_results_heading_visible():
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
        return bool(
            re.search(r"位於\s*台中市的?\s*\d+\s*間住宿", body_text)
        )
    except Exception:
        return False


def hotel_results_visible():
    return hotel_results_heading_visible() or bool(find_hotel_cards())


def collect_visible_hotels():
    for card in find_hotel_cards():
        try:
            visible = driver.execute_script("""
                const rect = arguments[0].getBoundingClientRect();
                return rect.bottom > 0 && rect.top < window.innerHeight;
            """, card)

            if not visible:
                continue

            name = ""
            for selector in [
                ".hotel-name",
                '[data-selenium="hotel-name"]',
                "h3",
                "h4",
            ]:
                name = next(
                    (
                        element.text.strip()
                        for element in card.find_elements(
                            By.CSS_SELECTOR, selector
                        )
                        if element.text.strip()
                    ),
                    "",
                )
                if name:
                    break

            price = ""
            for selector in [
                ".hotel-price-container .soft-red",
                ".hotel-price-container .price",
                '[data-selenium="display-price"]',
                '[data-selenium*="price"]',
            ]:
                price = next(
                    (
                        element.text.strip()
                        for element in card.find_elements(
                            By.CSS_SELECTOR, selector
                        )
                        if element.text.strip()
                    ),
                    "",
                )
                if price:
                    break

            if name and price:
                hotels[name] = [name, price]

        except Exception:
            continue


def save_csv():
    rows = list(hotels.values())

    try:
        with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["飯店名稱", "特價"])
            writer.writerows(rows)
        print("CSV 位置：", CSV_PATH)

    except PermissionError:
        new_path = CSV_PATH.with_name(
            f"agoda_result_{datetime.now():%Y%m%d_%H%M%S}.csv"
        )
        with open(new_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["飯店名稱", "特價"])
            writer.writerows(rows)
        print("原 CSV 無法覆寫，改存：", new_path)


try:
    stage = "開啟 Agoda"
    driver.get("https://www.agoda.com/zh-tw/")

    # 確認住宿分頁已選取
    stage = "確認住宿分頁"
    hotel_tab = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[role="tab"][data-element-name="all-rooms-tab"]')
        )
    )

    if hotel_tab.get_attribute("aria-selected") != "true":
        hotel_tab.click()
        wait.until(
            lambda d: hotel_tab.get_attribute("aria-selected") == "true"
        )

    print("目前分頁：", hotel_tab.text.strip())

    # 從住宿分頁找到住宿表單
    stage = "定位住宿表單"
    panel_id = hotel_tab.get_attribute("aria-controls")
    if not panel_id:
        raise RuntimeError("住宿分頁沒有 aria-controls，無法定位住宿表單。")

    panel = wait.until(
        EC.presence_of_element_located((By.ID, panel_id))
    )

    # 在住宿表單輸入台中
    stage = "輸入台中"
    destination = panel.find_element(
        By.CSS_SELECTOR, 'input[data-selenium="textInput"]'
    )
    wait.until(lambda d: destination.is_displayed() and destination.is_enabled())

    destination.click()
    destination.send_keys(Keys.CONTROL, "a")
    destination.send_keys("台中")

    # 等建議清單出現，實際點選畫面上的第一筆
    stage = "選取第一筆城市建議"
    city_result = WebDriverWait(driver, 20, poll_frequency=0.5).until(
        lambda d: find_first_city_suggestion(destination)
    )
    city_element, city_text = city_result
    print("選取第一筆建議：", city_text)
    driver.execute_script("arguments[0].click();", city_element)
    time.sleep(0.5)

    # 確認仍在住宿分頁
    if hotel_tab.get_attribute("aria-selected") != "true":
        raise RuntimeError("選取城市後住宿分頁不再是目前選取的分頁。")

    # 從住宿表單取得搜尋按鈕
    stage = "搜尋住宿"
    search_button = panel.find_element(
        By.CSS_SELECTOR, '[data-element-name="search-button"]'
    )
    wait.until(lambda d: search_button.is_enabled())

    # 記錄目前分頁，供搜尋後辨認新分頁
    old_handles = set(driver.window_handles)

    # 關閉可能出現的日期浮層，不會修改日期
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    time.sleep(0.3)

    # 點搜尋按鈕
    driver.execute_script("arguments[0].click();", search_button)

    # 等待並切換到搜尋結果新分頁
    stage = "切換搜尋結果分頁"
    new_handle = WebDriverWait(driver, 30, poll_frequency=0.5).until(
        lambda d: next(
            (
                handle
                for handle in d.window_handles
                if handle not in old_handles
            ),
            False,
        )
    )
    driver.switch_to.window(new_handle)
    print("已切換到新分頁：", driver.current_url)

    # 在新分頁等待住宿標題或飯店卡片
    stage = "等待飯店結果"
    results_wait = WebDriverWait(driver, 90, poll_frequency=1)
    results_wait.until(lambda d: hotel_results_visible())

    print("搜尋結果網址：", driver.current_url)
    print("已偵測到住宿結果，開始擷取。")

    # 滾動並擷取飯店資料
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

        no_new_rounds = no_new_rounds + 1 if added == 0 else 0
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
    print("飯店資料筆數：", len(hotels))

    try:
        driver.quit()
    except Exception:
        pass