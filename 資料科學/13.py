from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# momo 網址
url = 'https://www.momoshop.com.tw/main/Main.jsp?cid=memb&oid=back2hp&mdiv=1099800000-bt_0_150_01-bt_0_150_01_e1&ctype=B'

# 啟動 Chrome
driver = webdriver.Chrome()

try:
    print('正在開啟 momo...')
    driver.get(url)

    # 等待網頁載入
    time.sleep(3)

    # 顯示目前網址
    print('目前網址：', driver.current_url)

    # 尋找搜尋框
    search_box = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'input[type="text"]')
        )
    )

    print('找到搜尋框！')

    # 清除搜尋框
    search_box.clear()

    # 1. 自動輸入 NBA
    search_box.send_keys('nba')

    print('已輸入 nba')

    # 按 Enter
    search_box.send_keys(Keys.ENTER)

    # 等待搜尋結果
    time.sleep(5)

    print('搜尋完成！')
    print('搜尋結果網址：', driver.current_url)

    # 2. 儲存 HTML
    with open('NBA_test.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)

    print('已儲存：NBA_test.html')

except Exception as e:
    print('發生錯誤：', type(e).__name__)
    print('錯誤訊息：', e)

finally:
    time.sleep(2)
    driver.quit()
