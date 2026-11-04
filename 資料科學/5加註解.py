
# 匯入 Selenium 的 webdriver，用來控制 Chrome 瀏覽器
from selenium import webdriver

# 匯入 BeautifulSoup，用來解析網頁 HTML 原始碼
from bs4 import BeautifulSoup

# 匯入 Workbook，用來建立 Excel 活頁簿
from openpyxl import Workbook

# 匯入 Excel 儲存格格式工具：字型、背景顏色、文字對齊
from openpyxl.styles import Font, PatternFill, Alignment

# 匯入 get_column_letter，用來將欄位數字轉換成 Excel 欄位名稱
from openpyxl.utils import get_column_letter

# 匯入 re 正規表示式套件，用來搜尋及擷取排名與票房數字
import re

# 匯入 time 套件，用來控制程式等待網頁載入的時間
import time

# 匯入 os 套件，用來處理檔案及資料夾路徑
import os


# 設定台北週末票房排行榜的網站網址
START_URL = "https://app2.atmovies.com.tw/boxoffice/TWweekend/"

# 設定最後輸出的 Excel 檔案名稱
OUTPUT_FILE = "Taipei_movies.xlsx"


# 定義 clean_money 函式，負責清理票房文字並轉換成數字
def clean_money(text):

    # 將票房文字中的逗號移除，例如 4,019 變成 4019
    text = text.replace(",", "")

    # 使用正規表示式搜尋票房數字，允許前面有 $ 符號及空白
    match = re.search(r"\$?\s*(\d+(?:\.\d+)?)", text)

    # 如果有成功找到數字
    if match:

        # 取得擷取到的數字，並轉換成浮點數
        return float(match.group(1))

    # 如果沒有找到數字，就回傳 None
    return None


# 定義 main 主程式，負責執行整個爬蟲流程
def main():

    # 建立 Chrome 瀏覽器物件，讓 Selenium 控制瀏覽器
    driver = webdriver.Chrome()

    # 建立空清單，用來儲存擷取到的電影資料
    movies = []

    # 使用 try-finally，確保程式結束時會關閉瀏覽器
    try:

        # 在終端機顯示目前正在開啟網站
        print("正在開啟電影票房網站...")

        # 使用 Chrome 開啟台北週末票房排行榜
        driver.get(START_URL)

        # 等待 3 秒，讓網頁有時間載入資料
        time.sleep(3)

        # 取得目前網頁的 HTML 原始碼並交給 BeautifulSoup 解析
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 初始化 more_url，準備尋找完整票房排行榜的網址
        more_url = None

        # 使用迴圈尋找網頁中所有帶有 href 屬性的超連結
        for a in soup.find_all("a", href=True):

            # 取得目前超連結的網址
            href = a["href"]

            # 判斷網址是否包含 boxoffice 和 more，找出完整榜單連結
            if "/boxoffice/" in href and "/more/" in href:

                # 找到符合條件的網址後，儲存起來
                more_url = href

                # 找到後就停止搜尋，不必繼續檢查其他連結
                break

        # 如果有找到完整排行榜的網址
        if more_url:

            # 如果網址以 / 開頭，代表是相對路徑，需要補上網站網域
            if more_url.startswith("/"):

                # 將網站網域與相對路徑組合成完整網址
                more_url = "https://app2.atmovies.com.tw" + more_url

            # 如果網址不是以 http 開頭，也需要補上網站網域
            elif not more_url.startswith("http"):

                # 將網站網域與網址組合起來
                more_url = "https://app2.atmovies.com.tw/" + more_url

            # 使用瀏覽器開啟完整排行榜頁面
            driver.get(more_url)

            # 等待 3 秒，確保完整排行榜資料載入
            time.sleep(3)

        # 重新取得完整排行榜頁面的 HTML 原始碼
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 找出網頁中所有表格列，也就是 tr 標籤
        rows = soup.find_all("tr")

        # 使用 enumerate 逐列讀取資料，同時取得每一列的索引位置
        for i, row in enumerate(rows):

            # 找出目前這一列直接包含的 td 或 th 儲存格
            cells = row.find_all(["td", "th"], recursive=False)

            # 逐一取得每個儲存格的文字，並去除前後空白
            texts = [
                cell.get_text(" ", strip=True)
                for cell in cells
            ]

            # 如果這一列沒有任何文字，就跳過
            if not texts:
                continue

            # 取得第一個欄位的文字，預期這裡是電影排名
            rank_text = texts[0].strip()

            # 使用正規表示式確認第一個欄位是否為純數字
            if not re.fullmatch(r"\d+", rank_text):

                # 如果不是排名數字，就跳過這一列
                continue

            # 將排名文字轉換成整數
            rank = int(rank_text)

            # 只擷取排名 1 到 20 的電影
            if rank < 1 or rank > 20:

                # 如果排名不在範圍內，就跳過
                continue

            # 初始化電影名稱，預設為空字串
            title = ""

            # 從第二個儲存格開始尋找電影名稱
            for cell in cells[1:]:

                # 取得目前儲存格中的文字
                title = cell.get_text(" ", strip=True)

                # 如果有找到電影名稱，就停止尋找
                if title:
                    break

            # 如果電影名稱是空的，就跳過這筆資料
            if not title:
                continue

            # 電影名稱列與票房資料列可能分開
            # 因此需要往後尋找下一部電影出現之前的票房數字

            # 建立空清單，用來儲存找到的票房數字
            money_values = []

            # 從目前電影的下一列開始，逐列尋找票房資料
            for next_row in rows[i + 1:]:

                # 取得下一列直接包含的 td 或 th 儲存格
                next_cells = next_row.find_all(
                    ["td", "th"], recursive=False
                )

                # 取得下一列每個儲存格的文字內容
                next_texts = [
                    c.get_text(" ", strip=True)
                    for c in next_cells
                ]

                # 如果下一列沒有任何資料，就跳過
                if not next_texts:
                    continue

                # 如果第一個欄位又出現純數字，代表遇到下一部電影
                if re.fullmatch(r"\d+", next_texts[0].strip()):

                    # 停止尋找目前電影的票房資料
                    break

                # 將目前這一列的所有文字合併成一個字串
                row_text = " ".join(next_texts)

                # 使用正規表示式找出有 $ 符號的票房數字
                amounts = re.findall(
                    r"\$\s*[\d,]+(?:\.\d+)?", row_text
                )

                # 逐一處理找到的票房金額
                for amount in amounts:

                    # 呼叫 clean_money 函式，清除符號並轉換成數字
                    value = clean_money(amount)

                    # 如果成功取得數字
                    if value is not None:

                        # 將票房金額加入 money_values 清單
                        money_values.append(value)

            # 如果至少找到兩筆票房數字
            if len(money_values) >= 2:

                # 第一筆票房數字設定為本週票房
                weekly = money_values[0]

                # 第二筆票房數字設定為累計票房
                cumulative = money_values[1]

                # 將排名、電影名稱、本週票房及累計票房加入電影清單
                movies.append([
                    rank, title, weekly, cumulative
                ])

                # 在終端機印出電影排名、名稱及票房資訊
                print(
                    f"排名：{rank}｜{title}｜"
                    f"本週票房：{weekly:,.0f} 萬｜"
                    f"累計票房：{cumulative:,.0f} 萬"
                )

        # 建立字典，用來依照排名去除重複的電影資料
        unique_movies = {}

        # 逐筆讀取已經擷取的電影資料
        for movie in movies:

            # 使用電影排名作為字典的索引，避免相同排名重複出現
            unique_movies[movie[0]] = movie

        # 依照排名由小到大重新整理電影資料
        movies = [
            unique_movies[rank]
            for rank in sorted(unique_movies)
        ][:20]  # 最多只保留前 20 部電影

        # 如果最後沒有取得任何電影資料
        if not movies:

            # 顯示沒有抓到資料的錯誤訊息
            print("沒有抓到電影資料，請確認網站結構是否有變更。")

            # 結束 main 函式
            return

        # 建立一個新的 Excel 活頁簿
        wb = Workbook()

        # 取得 Excel 預設建立的第一個工作表
        ws = wb.active

        # 將工作表名稱設定為台北週末票房
        ws.title = "台北週末票房"

        # 設定 Excel 第一列的欄位名稱
        headers = [
            "排名",
            "電影名稱",
            "本週票房（萬新台幣）",
            "累計票房（萬新台幣）"
        ]

        # 將欄位名稱加入 Excel 工作表第一列
        ws.append(headers)

        # 逐筆讀取電影資料
        for movie in movies:

            # 將每部電影的資料寫入 Excel 下一列
            ws.append(movie)

        # 設定 Excel 第一列標題的外觀格式
        for cell in ws[1]:

            # 將標題文字設定為粗體，並使用白色字體
            cell.font = Font(bold=True, color="FFFFFF")

            # 將標題儲存格背景設定為藍色
            cell.fill = PatternFill(
                "solid", fgColor="4472C4"
            )

            # 將標題文字設定為水平置中
            cell.alignment = Alignment(horizontal="center")

        # 設定 Excel 四個欄位的寬度
        widths = [10, 65, 25, 25]

        # 使用 enumerate 依序取得欄位編號及設定的寬度
        for index, width in enumerate(widths, start=1):

            # 將數字欄位編號轉換成 Excel 欄位名稱，並設定欄寬
            ws.column_dimensions[
                get_column_letter(index)
            ].width = width

        # 從第二列開始，選取第三欄到第四欄的票房資料
        for row in ws.iter_rows(min_row=2, min_col=3, max_col=4):

            # 逐一處理每個票房儲存格
            for cell in row:

                # 設定數字顯示格式，加入千分位逗號
                cell.number_format = '#,##0'

        # 凍結第一列，向下捲動時仍然看得到欄位名稱
        ws.freeze_panes = "A2"

        # 開啟 Excel 自動篩選功能
        ws.auto_filter.ref = ws.dimensions

        # 設定 Excel 儲存位置為目前 Python 程式所在的資料夾
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            OUTPUT_FILE
        )

        # 將 Excel 活頁簿儲存到指定路徑
        wb.save(output_path)

        # 顯示爬蟲執行完成的訊息
        print("\n爬蟲完成！")

        # 顯示成功擷取的電影數量
        print(f"成功擷取 {len(movies)} 部電影")

        # 顯示 Excel 檔案的完整儲存位置
        print(f"Excel 儲存位置：{output_path}")

    # 不論程式是否發生錯誤，都會執行 finally
    finally:

        # 關閉 Chrome 瀏覽器並釋放相關資源
        driver.quit()


# 判斷目前程式是否為直接執行，而不是被其他程式匯入
if __name__ == "__main__":

    # 如果是直接執行這個 Python 檔案，就啟動 main 主程式
    main()
