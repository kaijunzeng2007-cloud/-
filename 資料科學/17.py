from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)

try:
    driver.get("https://github.com/login")

    wait.until(
        EC.visibility_of_element_located((By.ID, "login_field"))
    ).send_keys("yoby96321@gmail.com")

    driver.find_element(By.ID, "password").send_keys("yoby1111")
    driver.find_element(By.NAME, "commit").click()

    # 等待登入完成
    wait.until(lambda d: "/login" not in d.current_url)

    # 取得左側欄與中央動態區的文字
    left_sidebar = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".feed-left-sidebar")
        )
    )

    feed = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "feed-container")
        )
    )

    print("圖 1：左側欄")
    print(left_sidebar.text)

    print("\n圖 2：中央動態區")
    print(feed.text)

finally:
    driver.quit()