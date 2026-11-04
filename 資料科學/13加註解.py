
# 匯入 Selenium 的 webdriver，用來自動控制 Chrome 瀏覽器
from selenium import webdriver

# 匯入 By，用來指定尋找網頁元素的方式
from selenium.webdriver.common.by import By

# 匯入 Keys，用來模擬鍵盤按鍵，例如 Enter
from selenium.webdriver.common.keys import Keys

# 匯入 WebDriverWait，用來等待網頁元素出現或符合條件
from selenium.webdriver.support.ui import WebDriverWait

# 匯入 expected_conditions，提供網頁元素等待時的判斷條件
from selenium.webdriver.support import expected_conditions as EC

# 匯入 time 套件，用來控制程式等待的時間
import time


# 設定 momo 購物網站的網址
url = 'https://www.momoshop.com.tw/main/Main.jsp?cid=memb&oid=back2hp&mdiv=1099800000-bt_0_150_01-bt_0_150_01_e1&ctype=B'


# 使用 Selenium 啟動 Chrome 瀏覽器
driver = webdriver.Chrome()


# 使用 try 處理程式執行過程中可能發生的錯誤
try:

    # 在終端機顯示正在開啟 momo 網站
    print('正在開啟 momo...')

    # 使用 Chrome 瀏覽器開啟指定的 momo 網址
    driver.get(url)

    # 等待 3 秒，讓網站有時間載入
    time.sleep(3)

    # 取得並顯示目前瀏覽器所在的網址
    print('目前網址：', driver.current_url)

    # 使用 WebDriverWait 最多等待 15 秒，直到搜尋框可以被點擊
    search_box = WebDriverWait(driver, 15).until(

        # 使用 EC.element_to_be_clickable 確認搜尋框可以正常操作
        EC.element_to_be_clickable(

            # 使用 CSS Selector 尋找網頁中 type 屬性為 text 的輸入框
            (By.CSS_SELECTOR, 'input[type="text"]')
        )
    )

    # 顯示已經成功找到搜尋框
    print('找到搜尋框！')

    # 清除搜尋框原本可能存在的文字
    search_box.clear()

    # 1. 使用 send_keys() 在搜尋框中自動輸入 nba
    search_box.send_keys('nba')

    # 顯示已經成功輸入搜尋關鍵字
    print('已輸入 nba')

    # 使用 Keys.ENTER 模擬鍵盤按下 Enter 鍵
    # 送出搜尋請求
    search_box.send_keys(Keys.ENTER)

    # 等待 5 秒，讓網站有時間載入搜尋結果
    time.sleep(5)

    # 顯示搜尋已經完成的訊息
    print('搜尋完成！')

    # 取得並顯示搜尋完成後的網址
    print('搜尋結果網址：', driver.current_url)

    # 2. 使用 open() 建立 NBA_test.html 檔案
    # 'w' 代表寫入模式，encoding='utf-8' 用來處理中文編碼
    # 使用 with 可以在寫入完成後自動關閉檔案
    with open('NBA_test.html', 'w', encoding='utf-8') as f:

        # 使用 driver.page_source 取得目前網頁的 HTML 原始碼
        # 再使用 write() 將 HTML 原始碼寫入檔案
        f.write(driver.page_source)

    # 顯示 HTML 檔案已經成功儲存
    print('已儲存：NBA_test.html')


# 捕捉程式執行時可能發生的任何一般例外錯誤
except Exception as e:

    # 顯示發生錯誤的類型，例如 TimeoutException
    print('發生錯誤：', type(e).__name__)

    # 顯示詳細的錯誤訊息，方便檢查問題
    print('錯誤訊息：', e)


# finally 不論程式成功或發生錯誤，都會執行
finally:

    # 等待 2 秒，避免程式立即關閉瀏覽器
    time.sleep(2)

    # 關閉 Chrome 瀏覽器並釋放相關資源
    driver.quit()
