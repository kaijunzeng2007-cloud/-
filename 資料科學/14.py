
# 匯入正規表示式套件，用來處理文字及尋找球員背號
import re

# 匯入時間套件，用來等待網頁載入
import time

# 匯入 Path，用來設定電腦中的檔案路徑
from pathlib import Path

# pandas：讀取、整理及儲存 CSV 資料
import pandas as pd

# BeautifulSoup：解析網頁 HTML，擷取需要的資料
from bs4 import BeautifulSoup

# Selenium：控制 Chrome 瀏覽器，自動開啟網站
from selenium import webdriver

# WebDriverWait：等待網頁載入指定內容
from selenium.webdriver.support.ui import WebDriverWait

# TimeoutException：處理網頁載入逾時的情況
from selenium.common.exceptions import TimeoutException


# ==========================================
# 1. 設定 CSV 檔案位置
# ==========================================

# 取得目前使用者的桌面路徑
desktop = Path.home() / "Desktop"

# 設定全部球員薪資資料的 CSV 檔案位置
all_file = desktop / "all_play.csv"

# 設定最高薪前三名資料的 CSV 檔案位置
highest_file = desktop / "highest.csv"


# ==========================================
# 2. 將薪資文字轉換成數字
# ==========================================

# 定義函式，將薪資轉成可以比較大小的數字
def salary_number(value):

    # 使用正規表示式移除美元符號、逗號等非數字字元
    # 例如：$62,587,158 → 62587158
    text = re.sub(
        r"[^\d.]",
        "",
        str(value)
    )

    try:
        # 將處理後的文字轉換成浮點數
        return float(text)

    except ValueError:
        # 如果無法轉換成數字，就回傳 0
        return 0


# ==========================================
# 3. 將球員姓名轉換成 HoopsHype 網址
# ==========================================

# 定義函式，根據球員姓名產生個人薪資頁面網址
def get_player_url(name):

    # HoopsHype 排行榜有些球員使用名字縮寫
    # 例如 G. Antetokounmpo，需要改成完整姓名才能組合網址
    if name == "G. Antetokounmpo":
        name = "Giannis Antetokounmpo"

    # 將英文姓名轉成小寫，並移除句點
    slug = name.lower().replace(".", "")

    # 將姓名中間的空白轉換成連字號
    # 例如 Stephen Curry → stephen-curry
    slug = re.sub(r"\s+", "-", slug)

    # 回傳球員在 HoopsHype 的個人薪資頁面網址
    return f"https://hoopshype.com/player/{slug}/salary/"


# ==========================================
# 4. 從 HoopsHype 網站爬取球員背號
# ==========================================

# 定義函式，傳入瀏覽器物件及球員姓名
def get_player_number(driver, name):

    # 根據球員姓名取得個人頁面網址
    url = get_player_url(name)

    # 顯示目前正在查詢的球員及網址
    print(f"\n正在查詢：{name}")
    print("來源網址：", url)

    try:
        try:
            # 使用 Selenium 開啟球員個人頁面
            driver.get(url)

        except TimeoutException:
            # 如果網站載入太慢，仍嘗試讀取已經載入的內容
            print("網站載入較慢，繼續讀取...")

        # 最多等待 20 秒，直到網頁 HTML 長度超過 1000
        WebDriverWait(driver, 20).until(
            lambda d: len(d.page_source) > 1000
        )

        # 額外等待 1 秒，讓動態內容有時間顯示
        time.sleep(1)

        # 取得目前網頁的 HTML，交給 BeautifulSoup 解析
        soup = BeautifulSoup(
            driver.page_source,
            "html.parser"
        )

        # 擷取網頁中所有獨立文字
        # strip()：移除文字前後的空白
        # stripped_strings：取得 HTML 標籤中的文字內容
        lines = [
            text.strip()
            for text in soup.stripped_strings
            if text.strip()
        ]

        # 根據實際觀察的 HoopsHype 網頁：
        # 球員背號、位置、名字可能分開顯示
        #
        # 例如：
        # #7
        # PF
        # Giannis
        # Antetokounmpo
        #
        # 因此可以從球員姓氏附近尋找背號

        # 先取得球員完整姓名
        full_name = name

        # 將 Giannis 的縮寫還原成完整姓名
        if name == "G. Antetokounmpo":
            full_name = "Giannis Antetokounmpo"

        # 使用 split() 將姓名依空白切開
        # [-1] 取得最後一個單字，也就是球員姓氏
        # lower() 將姓氏轉成小寫，方便比對
        surname = full_name.split()[-1].lower()

        # 逐一檢查網頁中的文字
        # enumerate() 可以同時取得索引位置 i 和文字 text
        for i, text in enumerate(lines):

            # 判斷目前文字是否等於球員姓氏
            if text.lower() == surname:

                # 取得姓氏前面最多 8 段文字
                # max(0, i - 8) 避免索引超出開頭
                nearby = lines[
                    max(0, i - 8):i
                ]

                # 從最靠近姓氏的位置往前尋找背號
                for item in reversed(nearby):

                    # 使用正規表示式尋找 #30、#15、#7 等格式
                    # \d{1,2} 代表 1 到 2 位數字
                    # re.fullmatch() 要求整段文字符合格式
                    match = re.fullmatch(
                        r"#\s*(\d{1,2})",
                        item
                    )

                    # 如果找到符合格式的背號
                    if match:

                        # group(1) 取得括號內的數字
                        # 再加上 # 組成球衣背號
                        number = "#" + match.group(1)

                        # 顯示成功抓取的背號
                        print("成功爬取背號：", number)

                        # 回傳背號，並結束函式
                        return number

        # ======================================
        # 備用方式：從頁面開頭尋找背號
        # ======================================

        # 如果前面的姓氏比對找不到背號
        # 就搜尋網頁前 30 段文字
        for text in lines[:30]:

            # 檢查文字是否符合 #數字 的格式
            match = re.fullmatch(
                r"#\s*(\d{1,2})",
                text
            )

            if match:

                # 取得找到的背號
                number = "#" + match.group(1)

                # 顯示成功訊息
                print("成功爬取背號：", number)

                # 回傳背號
                return number

        # 如果兩種方式都找不到，就顯示訊息
        print("找不到球員背號")

    except Exception as error:

        # 如果爬蟲發生錯誤，顯示錯誤類型和內容
        # 避免整個程式因單一球員查詢失敗而中斷
        print(
            "爬取背號失敗：",
            type(error).__name__,
            str(error)
        )

    # 如果沒有成功取得背號，就回傳「未找到」
    return "未找到"


# ==========================================
# 5. 主程式：讀取球員薪資資料
# ==========================================

# 先將瀏覽器變數設為 None
# 避免瀏覽器尚未啟動時，關閉瀏覽器發生錯誤
driver = None

try:

    # 使用 pandas 讀取之前已經爬取完成的 CSV
    df = pd.read_csv(
        all_file,

        # utf-8-sig 可以避免 Excel 開啟中文時出現亂碼
        encoding="utf-8-sig",

        # 將所有欄位以字串方式讀取
        dtype=str,

        # 保留原始空白內容，不自動轉成 NaN
        keep_default_na=False
    )

    # 顯示讀取成功訊息及球員總數
    print("成功讀取 all_play.csv")
    print("球員總數：", len(df))

    # 取得第二欄的名稱，代表球員姓名
    name_col = df.columns[1]

    # 取得第三欄的名稱，代表當季薪資
    salary_col = df.columns[2]

    # ======================================
    # 6. 找出薪資最高的前三名球員
    # ======================================

    # 新增一個暫時使用的薪資數字欄位
    # apply() 會對每筆薪資執行 salary_number 函式
    df["_salary_number"] = df[salary_col].apply(
        salary_number
    )

    # 根據薪資數字由大到小排序
    # ascending=False 代表降冪排序
    # head(3) 代表只取前三筆資料
    top3 = df.sort_values(
        by="_salary_number",
        ascending=False
    ).head(3)

    # ======================================
    # 7. 啟動 Selenium 瀏覽器
    # ======================================

    # 建立 Chrome 瀏覽器設定
    options = webdriver.ChromeOptions()

    # eager：網頁主要 HTML 載入完成後即可繼續
    # 不必等待所有圖片、廣告等資源載入
    options.page_load_strategy = "eager"

    # 將 Chrome 視窗最大化
    options.add_argument("--start-maximized")

    # 啟動 Chrome 瀏覽器
    driver = webdriver.Chrome(options=options)

    # 設定網頁載入最多等待 30 秒
    driver.set_page_load_timeout(30)

    # 建立空清單，用來存放最高薪前三名資料
    highest_players = []

    # ======================================
    # 8. 逐一爬取前三名球員背號
    # ======================================

    # iterrows() 可以逐列讀取 DataFrame
    # _ 代表不使用該列的索引值
    # row 代表目前球員的整列資料
    for _, row in top3.iterrows():

        # 取得球員姓名並移除前後空白
        name = str(row[name_col]).strip()

        # 取得球員薪資並移除前後空白
        salary = str(row[salary_col]).strip()

        # 呼叫自訂函式，透過 Selenium 和 BeautifulSoup
        # 從 HoopsHype 球員頁面取得背號
        number = get_player_number(
            driver,
            name
        )

        # 將球員姓名、背號及薪資加入清單
        highest_players.append({
            "Player": name,
            "Number": number,
            "Salary": salary
        })

    # ======================================
    # 9. 將前三名資料轉換成 DataFrame
    # ======================================

    # 建立新的 DataFrame
    # 並指定輸出欄位順序
    highest_df = pd.DataFrame(
        highest_players,
        columns=[
            "Player",
            "Number",
            "Salary"
        ]
    )

    # ======================================
    # 10. 儲存 highest.csv
    # ======================================

    # 將最高薪前三名資料儲存成 CSV
    highest_df.to_csv(
        highest_file,

        # 不輸出 pandas 自動產生的索引欄位
        index=False,

        # 使用 utf-8-sig，方便 Excel 正常開啟
        encoding="utf-8-sig"
    )

    # ======================================
    # 11. 顯示最終結果
    # ======================================

    # 印出標題
    print("\n========== 薪資最高前三名 ==========")

    # 顯示 DataFrame 全部內容
    # index=False 代表不顯示索引編號
    print(
        highest_df.to_string(index=False)
    )

    # 顯示儲存成功訊息
    print("\n已儲存 highest.csv")

    # 顯示資料來源
    print("資料來源：HoopsHype")


# ==========================================
# 12. 錯誤處理
# ==========================================

except FileNotFoundError:

    # 如果桌面上找不到 all_play.csv
    print("找不到桌面上的 all_play.csv")

except PermissionError:

    # 如果 CSV 正在被 Excel 使用，可能無法覆寫
    print("請先關閉 Excel 中開啟的 highest.csv")

except Exception as error:

    # 處理其他未預期的程式錯誤
    print(
        "程式執行錯誤：",
        type(error).__name__,
        str(error)
    )


# ==========================================
# 13. 關閉瀏覽器
# ==========================================

finally:

    # 如果 Selenium 已經成功啟動 Chrome
    if driver:

        # 關閉瀏覽器並釋放資源
        driver.quit()
