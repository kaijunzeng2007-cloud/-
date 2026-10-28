
import re  # 正規表示式，用來搜尋文字、清理空白及找出背號
import time  # 控制等待時間，讓網頁有時間載入
from pathlib import Path  # 處理檔案路徑及儲存 HTML
from urllib.parse import urljoin  # 將相對網址轉換成完整網址

import pandas as pd  # 處理表格資料、排序及輸出 CSV
from bs4 import BeautifulSoup  # 解析 HTML 網頁內容
from selenium import webdriver  # 使用瀏覽器自動化操作網頁
from selenium.webdriver.edge.options import Options  # 設定 Edge 瀏覽器
from selenium.webdriver.support.ui import WebDriverWait  # 等待網頁元素載入

# 設定要爬取的 NBA 球員薪資網頁
URL = "https://hoopshype.com/salaries/players/"

# 建立 Edge 瀏覽器設定
options = Options()

# 啟動 Edge 瀏覽器
driver = webdriver.Edge(options=options)

# 設定最多等待 25 秒
wait = WebDriverWait(driver, 25)


# 定義清理文字的函式
def clean_text(value):
    # 將連續空白、換行符號轉成一個空白，並移除前後空白
    return re.sub(r"\s+", " ", str(value or "")).strip()


# 定義薪資轉換函式
def salary_number(value):
    # 移除薪資中的 $、逗號等非數字符號
    text = re.sub(r"[^\d.]", "", str(value))

    try:
        # 將薪資轉換成浮點數，方便進行大小比較
        return float(text)

    except ValueError:
        # 如果無法轉換成數字，就回傳 None
        return None


# 定義儲存 CSV 檔案的函式
def save_csv(data, filename):
    # 建立檔案路徑物件
    path = Path(filename)

    # 最多嘗試 100 次，避免檔案被占用
    for i in range(100):

        # 第一次使用原本檔名
        # 如果被占用，就依序增加 _1、_2 等編號
        target = (
            path if i == 0
            else path.with_name(
                f"{path.stem}_{i}{path.suffix}"
            )
        )

        try:
            # 將 DataFrame 資料輸出成 CSV
            data.to_csv(
                target,
                index=False,  # 不輸出 DataFrame 的索引
                encoding="utf-8-sig"  # 避免 Excel 開啟中文時出現亂碼
            )

            # 顯示成功輸出的檔案名稱
            print(f"已輸出 {target}")
            return

        except PermissionError:
            # 如果檔案正在被 Excel 使用，就嘗試其他檔名
            continue

    # 如果嘗試 100 次仍失敗，就顯示錯誤
    raise Exception("無法儲存 CSV，請關閉 Excel")


# 定義從文字中找出球員背號的函式
def extract_number(text):
    # 清理文字中的多餘空白
    text = clean_text(text)

    # 使用正規表示式尋找 #30、#15 這類背號
    match = re.search(
        r"(?:^|\s)#\s*(\d{1,2})(?!\d)",
        text
    )

    # 如果找到符合格式的背號
    if match:
        # group(1) 取得括號內的數字
        return match.group(1)

    # 如果沒有 # 符號，就嘗試尋找 jersey 或 number
    match = re.search(
        r"(?:jersey\s*number|jersey|number)"
        r"\s*:?\s*#?\s*(\d{1,2})\b",
        text,
        re.I  # 忽略英文大小寫
    )

    # 如果找到背號，就回傳數字
    if match:
        return match.group(1)

    # 如果都找不到，就回傳空字串
    return ""


# 定義從球員個人頁面尋找背號的函式
def find_number(soup, player_name):

    # 取出球員姓氏並轉成小寫
    # 避免姓名縮寫與完整姓名不同
    last_name = clean_text(
        player_name
    ).split()[-1].lower()

    # 第一種方法：從球員姓名標題尋找
    for tag in soup.find_all(
        ["h1", "h2", "h3", "h4"]
    ):

        # 取得標題文字
        heading = clean_text(
            tag.get_text(" ", strip=True)
        )

        # 如果標題不包含球員姓氏，就跳過
        if last_name not in heading.lower():
            continue

        # 先檢查標題本身有沒有背號
        number = extract_number(heading)

        # 找到背號就直接回傳
        if number:
            return number

        # 如果標題沒有背號，就往上一層 HTML 元素尋找
        parent = tag.parent

        # 最多往上搜尋四層
        for _ in range(4):

            # 如果已經沒有上一層，就停止
            if parent is None:
                break

            # 尋找區塊內的 span、div、p、strong 元素
            for element in parent.find_all(
                ["span", "div", "p", "strong"]
            ):

                # 取得元素文字
                text = clean_text(
                    element.get_text(" ", strip=True)
                )

                # 排除太長的文字，減少抓錯資料的機率
                if len(text) > 100:
                    continue

                # 從文字中尋找背號
                number = extract_number(text)

                # 找到背號就回傳
                if number:
                    return number

            # 繼續往上一層搜尋
            parent = parent.parent

    # 第二種方法：搜尋其他包含球員姓氏的元素
    for tag in soup.find_all(
        string=re.compile(
            re.escape(last_name),
            re.I
        )
    ):

        # 取得該文字所在的 HTML 元素
        parent = tag.parent

        # 最多往上搜尋三層
        for _ in range(3):

            if parent is None:
                break

            # 取得該區塊的文字
            text = clean_text(
                parent.get_text(" ", strip=True)
            )

            # 限制文字長度，避免搜尋範圍太大
            if len(text) <= 150:

                # 嘗試尋找背號
                number = extract_number(text)

                if number:
                    return number

            # 繼續往上一層
            parent = parent.parent

    # 如果兩種方法都找不到，就回傳空字串
    return ""


# 主程式開始
try:
    print("正在開啟 HoopsHype...")

    # 使用 Selenium 開啟 NBA 薪資網頁
    driver.get(URL)

    # 等待網頁的表格資料出現
    wait.until(
        lambda d: len(
            BeautifulSoup(
                d.page_source,
                "html.parser"
            ).select("table tbody tr")
        ) > 0
    )

    # 取得 Selenium 載入後的 HTML
    # 再交給 BeautifulSoup 解析
    soup = BeautifulSoup(
        driver.page_source,
        "html.parser"
    )

    # 找出網頁中的第一個 table 表格
    table = soup.find("table")

    # 如果找不到表格，就顯示錯誤
    if table is None:
        raise Exception("找不到薪資表格")

    # 抓取表格標題
    headers = [
        clean_text(
            th.get_text(" ", strip=True)
        )
        for th in table.select("thead th")
    ]

    # 建立空清單，用來儲存表格資料
    rows = []

    # 建立空字典，用來儲存球員姓名與個人頁面網址
    player_links = {}

    # 逐列讀取表格資料
    for tr in table.select("tbody tr"):

        # 取得每一列中的儲存格文字
        cells = [
            clean_text(
                td.get_text(" ", strip=True)
            )
            for td in tr.find_all(
                ["th", "td"],
                recursive=False  # 只抓取直接子元素
            )
        ]

        # 如果這一列沒有資料，就跳過
        if not cells:
            continue

        # 將這一列資料加入 rows 清單
        rows.append(cells)

        # 尋找這一列中所有包含網址的 a 標籤
        for a in tr.select("a[href]"):

            # 取得球員名稱
            name = clean_text(
                a.get_text(" ", strip=True)
            )

            # 取得超連結網址
            href = a.get("href", "")

            # 如果姓名和網址都存在
            if name and href:

                # 將球員姓名與完整網址存入字典
                player_links[name.lower()] = urljoin(
                    URL, href
                )

    # 如果沒有抓到任何資料，就停止
    if not rows:
        raise Exception("沒有抓到資料")

    # 如果標題數量與資料欄位數量相同
    if headers and len(headers) == len(rows[0]):

        # 使用網頁原本的標題建立 DataFrame
        df = pd.DataFrame(
            rows,
            columns=headers
        )

    else:
        # 如果標題數量不同，就使用預設欄位編號
        df = pd.DataFrame(rows)

    # 顯示成功抓取的資料筆數
    print(f"成功抓取 {len(df)} 筆資料")

    # 將全部薪資表格輸出成 all_play.csv
    save_csv(df, "all_play.csv")

    # 尋找球員姓名所在的欄位
    name_col = next(
        (
            c for c in df.columns
            if "player" in str(c).lower()
        ),
        df.columns[0]  # 找不到時使用第一欄
    )

    # 尋找薪資欄位
    salary_cols = [
        c for c in df.columns
        if re.search(
            r"2026|2027|salary",
            str(c),
            re.I
        )
    ]

    # 如果找不到薪資欄位，就顯示錯誤
    if not salary_cols:
        raise Exception("找不到薪資欄位")

    # 使用找到的第一個薪資欄位
    salary_col = salary_cols[0]

    # 將薪資轉換成數字，建立新的 _salary 欄位
    df["_salary"] = df[salary_col].apply(
        salary_number
    )

    # 將球員依照薪資由高到低排序
    top3 = (
        df.dropna(subset=["_salary"])  # 排除沒有薪資的球員
        .sort_values(
            "_salary",
            ascending=False  # False 代表由大到小
        )
        .head(3)  # 只取前三筆資料
    )

    # 如果有效薪資不足三筆，就停止
    if len(top3) < 3:
        raise Exception("薪資資料不足三筆")

    # 建立空清單，用來儲存前三名球員的背號
    numbers = []

    # 逐一處理前三名球員
    for name in top3[name_col]:

        # 清理球員姓名
        name = clean_text(name)

        print(
            f"\n正在抓取 {name} 的背號..."
        )

        # 從字典中取得球員個人頁面網址
        player_url = player_links.get(
            name.lower()
        )

        # 如果沒有找到球員網址
        if not player_url:
            print("找不到球員個人頁面")

            # 用空字串表示沒有背號
            numbers.append("")
            continue

        try:
            # 使用 Selenium 開啟球員個人頁面
            driver.get(player_url)

            # 等待四秒，讓網頁資料載入
            time.sleep(4)

            # 使用 BeautifulSoup 解析球員頁面
            player_soup = BeautifulSoup(
                driver.page_source,
                "html.parser"
            )

            # 呼叫 find_number 函式尋找背號
            number = find_number(
                player_soup,
                name
            )

            # 如果成功找到背號
            if number:
                print(f"{name}：#{number}")

            else:
                # 如果找不到背號
                print(f"{name}：找不到背號")

                # 將姓名中的特殊符號改成底線
                # 避免檔案名稱出現不合法字元
                safe_name = re.sub(
                    r"[^a-zA-Z0-9]+",
                    "_",
                    name
                )

                # 建立除錯用 HTML 檔案名稱
                debug_file = (
                    f"debug_{safe_name}.html"
                )

                # 儲存網頁原始碼，方便之後檢查
                Path(debug_file).write_text(
                    driver.page_source,
                    encoding="utf-8"
                )

                print(
                    f"已儲存檢查檔案：{debug_file}"
                )

            # 將抓到的背號加入 numbers 清單
            numbers.append(number)

        except Exception as error:
            # 如果抓取過程發生錯誤，顯示錯誤訊息
            print(f"抓取失敗：{error}")

            # 加入空字串，避免資料數量不一致
            numbers.append("")

    # 建立最高薪前三名的 DataFrame
    highest = pd.DataFrame({
        "Player": top3[name_col].values,  # 球員姓名
        "Number": numbers,  # 球員背號
        "Salary": top3[salary_col].values  # 球員薪資
    })

    # 在終端機顯示前三名資料
    print("\n薪資最高前三名：")
    print(
        highest.to_string(index=False)
    )

    # 將前三名資料輸出成 highest.csv
    save_csv(highest, "highest.csv")

    # 檢查是否有球員沒有抓到背號
    if highest["Number"].eq("").any():

        print(
            "\n部分背號未抓到，"
            "請提供 debug HTML 檔案。"
        )

    else:
        # 如果三個背號都不為空
        print("\n三位球員背號全部抓取完成！")

    print("\n程式執行完成！")

except Exception as error:
    # 處理主程式執行時發生的錯誤
    print(f"\n程式發生錯誤：{error}")

finally:
    # 無論程式成功或失敗，都會關閉瀏覽器
    # 避免 Edge 持續在背景執行
    driver.quit()
