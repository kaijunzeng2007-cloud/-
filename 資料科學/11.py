
import os
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# 商品列表的來源網址。
URL = "https://fchart.github.io/ML/nba_items.html"

# CSV 儲存在 Python 程式所在資料夾
folder = os.path.dirname(os.path.abspath(__file__))

# Chrome 設定
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)
# 每次呼叫 until 時最多等待 15 秒，條件成立就立即繼續。
wait = WebDriverWait(driver, 15)

# total 累計已寫入的商品筆數；page 記錄目前處理的頁碼。
total = 0
page = 1

try:
    driver.get(URL)

    # 等待商品表格載入
    wait.until(
        lambda d: len(
            d.find_elements(By.CSS_SELECTOR, "#table-body tr")
        ) > 0
    )

    # 持續處理分頁，直到找不到下一頁按鈕時以 break 結束。
    while True:
        # 取得目前頁面的所有商品
        rows = driver.find_elements(
            By.CSS_SELECTOR, "#table-body tr"
        )

        products = []

        for row in rows:
            # 每一列預期有三個儲存格：商品編號、商品名稱、價格。
            cols = row.find_elements(By.TAG_NAME, "td")

            # 只處理欄位數正確的列，strip() 去掉文字前後空白。
            if len(cols) == 3:
                product = [
                    cols[0].text.strip(),
                    cols[1].text.strip(),
                    cols[2].text.strip()
                ]

                products.append(product)

                print("商品編號:", product[0])
                print("商品名稱:", product[1])
                print("價格:", product[2])
                print("-" * 50)

        # 沒有有效資料時主動報錯，避免誤以為已成功匯出該頁。
        if not products:
            raise RuntimeError(
                f"第 {page} 頁沒有取得商品資料"
            )

        # 每頁儲存成不同的 CSV
        filename = os.path.join(
            folder, f"NBA_Products{page}.csv"
        )

        # w 會覆寫同名檔案；newline="" 避免多餘空白列。
        # utf-8-sig 加入 BOM，方便 Excel 正確顯示中文。
        with open(
            filename, "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.writer(file)

            # 先寫入標題列，再一次寫入本頁的所有商品。
            writer.writerow([
                "商品編號", "商品名稱", "價格"
            ])

            writer.writerows(products)

        # 只在本頁 CSV 寫入成功後，才累加商品數量。
        total += len(products)

        print(f"儲存頁面: {page}")
        print()

        # 尋找下一頁按鈕
        next_buttons = driver.find_elements(
            By.CSS_SELECTOR, "#pagination-wrapper .nextbtn"
        )

        # 沒有下一頁代表全部完成
        if not next_buttons:
            break

        # 預先算出下一頁頁碼，供點擊後的等待條件確認。
        next_page = page + 1

        # 點擊下一頁
        next_buttons[0].click()

        # 等待分頁切換完成
        # 讀取網頁 JavaScript 的 state.page，確認網站已切換到預期頁碼。
        wait.until(
            lambda d: d.execute_script(
                "return state.page"
            ) == next_page
        )

        # 頁碼更新後，再確認表格至少有一列資料可供擷取。
        wait.until(
            lambda d: len(
                d.find_elements(
                    By.CSS_SELECTOR, "#table-body tr"
                )
            ) > 0
        )

        page = next_page

    print("=" * 50)
    print(f"總共儲存頁面: {page}")
    print(f"總商品筆數: {total}")
    print(f"CSV 儲存位置: {folder}")
    print("=" * 50)

# 即使載入、解析或寫檔途中發生例外，也確保關閉瀏覽器。
finally:
    driver.quit()
