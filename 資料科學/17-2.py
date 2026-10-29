
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)

# 手動填入自己的 GitHub Cookie
cookies = [
    {
        "name": "user_session",
        "value": "VVQzrY6WyCaVNN5nRFjF19qRpfWpkdGJvHaP7-WhJFPa4vi1",
        "domain": ".github.com",
        "path": "/"
    },
]

try:
    # 1. 先開啟 GitHub，建立 Cookie 所屬網域
    driver.get("https://github.com/")

    # 2. 手動塞入 Cookie
    for cookie in cookies:
        driver.add_cookie(cookie)

    # 3. 重新載入，套用登入狀態
    driver.get("https://github.com/")

    # 4. 等待登入完成：確認不在登入頁，且頁面已載入
    wait.until(lambda d: "/login" not in d.current_url)

    # 5. 確認是否真的登入
    time.sleep(2)

    if driver.find_elements(
        By.CSS_SELECTOR, 'a[href="/login"]'
    ):
        print("可能尚未登入，請檢查 Cookie 是否有效。")
    else:
        print("已離開登入頁，繼續擷取頁面內容。")

    # 6. 等待左側欄
    try:
        left_sidebar = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".feed-left-sidebar")
            )
        )
    except Exception:
        left_sidebar = None

    # 7. 等待中央動態區
    try:
        feed = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "feed-container")
            )
        )
    except Exception:
        feed = None

    time.sleep(3)

    # 8. 印出左側欄
    print("\n圖 1：左側欄")
    if left_sidebar:
        print(left_sidebar.text)
    else:
        print("找不到左側欄，可能是網頁結構已變更。")

    # 9. 印出中央動態區
    print("\n圖 2：中央動態區")
    if feed:
        print(feed.text)
    else:
        print("找不到中央動態區，請檢查 CSS 選擇器。")


finally:
    driver.quit()
