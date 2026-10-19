
import re  # 使用正規表示式整理文字
import pandas as pd  # 建立表格與輸出 CSV
from bs4 import BeautifulSoup  # 解析 HTML
from selenium import webdriver  # 操作 Chrome 瀏覽器
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# 臺灣銀行最新匯率網站
url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"

# 設定 Chrome 瀏覽器
options = Options()
options.add_argument("--start-maximized")

# 開啟 Chrome
driver = webdriver.Chrome(options=options)


# 清除文字中多餘的空白
def clean_text(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


# 取得幣別名稱
def get_currency(cell):

    # 優先尋找網頁中完整的幣別名稱
    selectors = [
        ".visible-phone",
        ".visible-print",
        ".hidden-phone",
        ".currency",
        "a"
    ]

    for selector in selectors:
        tag = cell.select_one(selector)

        if tag:
            text = clean_text(
                tag.get_text(" ", strip=True)
            )

            # 確認包含幣別代碼，例如 USD
            match = re.search(
                r"([\u4e00-\u9fff]+)\s*\(([A-Z]{3})\)",
                text
            )

            if match:
                return f"{match.group(1)} ({match.group(2)})"

    # 如果標籤沒有抓到，就抓整個儲存格
    text = clean_text(
        cell.get_text(" ", strip=True)
    )

    # 從完整文字中尋找幣別名稱與代碼
    match = re.search(
        r"([\u4e00-\u9fff]+)\s*\(([A-Z]{3})\)",
        text
    )

    if match:
        return f"{match.group(1)} ({match.group(2)})"

    # 若幣別名稱不存在，嘗試尋找代碼
    code_match = re.search(
        r"\b[A-Z]{3}\b",
        text
    )

    if code_match:
        return code_match.group(0)

    return "未知幣別"


try:
    print("正在開啟臺灣銀行最新匯率網站...")

    # 使用 Selenium 開啟網站
    driver.get(url)

    # 等待匯率資料列出現
    try:
        WebDriverWait(driver, 30).until(
            lambda d: len(
                d.find_elements(By.CSS_SELECTOR, "table tbody tr")
            ) > 0
        )
    except Exception:
        print("尚未偵測到匯率表格。")
        print("如果出現安全驗證，請先在 Chrome 完成驗證。")
        input("完成後按 Enter 繼續：")

    # 取得網頁 HTML
    html = driver.page_source

    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html, "html.parser")

    # 尋找匯率表格
    rate_table = None

    for table in soup.find_all("table"):
        table_text = clean_text(
            table.get_text(" ", strip=True)
        )

        if "現金" in table_text and "即期" in table_text:
            rate_table = table
            break

    if rate_table is None:
        print("找不到匯率表格，請確認網站是否正常開啟。")

    else:
        # 建立空清單儲存資料
        bank_data = []

        # 找出匯率表格的每一列
        rows = rate_table.select("tbody tr")

        for row in rows:

            # 取得這一列的所有儲存格
            cells = row.find_all("td", recursive=False)

            # 至少需要幣別加四個匯率欄位
            if len(cells) < 5:
                continue

            # 取得幣別
            currency = get_currency(cells[0])

            # 取得四種匯率
            rates = []

            for cell in cells[1:5]:
                rates.append(
                    clean_text(
                        cell.get_text(" ", strip=True)
                    )
                )

            # 儲存這一列的資料
            bank_data.append({
                "幣別": currency,
                "現金買入": rates[0],
                "現金賣出": rates[1],
                "即期買入": rates[2],
                "即期賣出": rates[3],
                "遠期匯率": "查詢",
                "歷史匯率": "查詢"
            })

        # 將資料轉換成 pandas 表格
        df = pd.DataFrame(
            bank_data,
            columns=[
                "幣別",
                "現金買入",
                "現金賣出",
                "即期買入",
                "即期賣出",
                "遠期匯率",
                "歷史匯率"
            ]
        )

        if df.empty:
            print("沒有抓到匯率資料。")

        else:
            # 儲存老師要求的 bank.csv
            df.to_csv(
                "bank.csv",
                index=False,
                encoding="utf-8-sig"
            )

            # 設定終端機顯示寬度
            pd.set_option("display.width", 200)
            pd.set_option("display.max_rows", None)

            # 顯示所有資料
            print("\n========== 臺灣銀行最新匯率 ==========")
            print(df.to_string(index=False))

            # 顯示抓取結果
            print(f"\n成功抓取 {len(df)} 種幣別")
            print("已成功儲存 bank.csv")

            # 檢查是否有未知幣別
            unknown = (df["幣別"] == "未知幣別").sum()

            if unknown > 0:
                print(f"注意：有 {unknown} 筆幣別尚未正確辨識。")

except Exception as error:
    print("程式執行發生錯誤：", error)

finally:
    # 關閉 Chrome 瀏覽器
    driver.quit()
