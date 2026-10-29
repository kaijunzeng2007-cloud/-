
import os
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://fchart.github.io/ML/nba_items.html"

# CSV 儲存在 Python 程式所在資料夾
folder = os.path.dirname(os.path.abspath(__file__))

# Chrome 設定
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

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

    while True:
        # 取得目前頁面的所有商品
        rows = driver.find_elements(
            By.CSS_SELECTOR, "#table-body tr"
        )

        products = []

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")

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

        if not products:
            raise RuntimeError(
                f"第 {page} 頁沒有取得商品資料"
            )

        # 每頁儲存成不同的 CSV
        filename = os.path.join(
            folder, f"NBA_Products{page}.csv"
        )

        with open(
            filename, "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "商品編號", "商品名稱", "價格"
            ])

            writer.writerows(products)

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

        next_page = page + 1

        # 點擊下一頁
        next_buttons[0].click()

        # 等待分頁切換完成
        wait.until(
            lambda d: d.execute_script(
                "return state.page"
            ) == next_page
        )

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

finally:
    driver.quit()
