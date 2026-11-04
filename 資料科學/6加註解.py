
# 匯入 requests 套件，用來向網站發送 HTTP 請求及下載網頁資料
import requests

# 匯入 BeautifulSoup，用來解析 HTML 網頁內容
from bs4 import BeautifulSoup

# 匯入 csv 套件，用來建立及寫入 CSV 檔案
import csv

# 匯入 os 套件，用來處理檔案及資料夾路徑
import os

# 匯入 time 套件，用來控制程式等待時間
import time

# 匯入 random 套件，用來產生隨機等待秒數
import random


# 設定要爬取的 NBA 球隊代碼
# CLE 代表克里夫蘭騎士隊
# HOU 代表休士頓火箭隊
# GSW 代表金州勇士隊
TEAMS = ["CLE", "HOU", "GSW"]

# 設定 Basketball Reference 的球隊資料網址
# {0} 是預留位置，之後會替換成不同的球隊代碼
URL = "https://www.basketball-reference.com/teams/{0}/2024.html"

# 取得目前 Python 程式所在的資料夾路徑
folder = os.path.dirname(os.path.abspath(__file__))

# 組合資料夾路徑與 CSV 檔案名稱
# 最後會將檔案儲存在 Python 程式所在的資料夾
filename = os.path.join(folder, "players.csv")

# 設定 CSV 檔案第一列的欄位名稱
headers = ["球隊", "背號", "姓名", "位置", "體重", "生日", "經驗", "大學"]

# 建立空清單，用來儲存所有球隊的球員資料
players = []

# 設定 HTTP 請求標頭，模擬一般瀏覽器傳送請求
http_headers = {

    # 設定 User-Agent，讓網站辨識目前的請求來源為瀏覽器
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "

                  # 繼續設定瀏覽器的核心資訊
                  "AppleWebKit/537.36 (KHTML, like Gecko) "

                  # 設定 Chrome 瀏覽器版本資訊
                  "Chrome/120.0.0.0 Safari/537.36",

    # 設定網站回傳內容的語言偏好，優先使用繁體中文
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

# 建立 requests Session 物件，讓多次請求可以共用連線設定
session = requests.Session()

# 將前面設定的 HTTP 標頭加入 Session
session.headers.update(http_headers)

# 使用 for 迴圈，依序爬取 TEAMS 清單中的每一支球隊
for team in TEAMS:

    # 使用 try 處理可能發生的網路錯誤
    try:

        # 使用 format(team) 將網址中的 {0} 替換成目前球隊代碼
        # 使用 get() 發送 HTTP GET 請求
        # timeout=30 表示最多等待 30 秒
        response = session.get(URL.format(team), timeout=30)

        # 檢查網站回應狀態，如果 HTTP 請求失敗就產生例外
        response.raise_for_status()

        # 使用 BeautifulSoup 解析網站回傳的 HTML 原始碼
        # html.parser 是 Python 內建的 HTML 解析器
        soup = BeautifulSoup(response.text, "html.parser")

        # 尋找 HTML 中 id 為 roster 的表格
        # 這個表格存放球隊的球員名單
        table = soup.find("table", id="roster")

        # 如果找不到球員名單表格
        if table is None:

            # 顯示目前球隊找不到球員名單的訊息
            print(f"{team}：找不到球員名單")

            # 跳過目前球隊，繼續處理下一支球隊
            continue

        # 在球員名單表格中尋找 tbody 標籤
        # tbody 通常存放表格中的實際資料列
        tbody = table.find("tbody")

        # 如果找不到 tbody
        if tbody is None:

            # 顯示目前球隊找不到球員資料的訊息
            print(f"{team}：找不到球員資料")

            # 跳過目前球隊，繼續處理下一支球隊
            continue

        # 設定目前球隊成功擷取的球員數量，初始值為 0
        count = 0

        # 使用迴圈讀取 tbody 中的所有 tr 標籤
        # 每一個 tr 代表表格中的一列資料
        for tr in tbody.find_all("tr"):

            # 定義 get_data 函式，用來取得指定欄位的球員資料
            def get_data(stat):

                # 尋找目前球員資料列中符合 data-stat 名稱的 th 或 td 儲存格
                cell = tr.find(["th", "td"], attrs={"data-stat": stat})

                # 如果找到儲存格，就取得文字並移除前後空白
                # 如果沒有找到，就回傳空字串
                return cell.get_text(" ", strip=True) if cell else ""

            # 取得球員背號
            number = get_data("number")

            # 取得球員姓名
            name = get_data("player")

            # 取得球員場上位置
            position = get_data("pos")

            # 取得球員體重
            weight = get_data("weight")

            # 取得球員出生日期
            birthday = get_data("birth_date")

            # 取得球員在 NBA 的經驗年數
            experience = get_data("years_experience")

            # 取得球員就讀的大學名稱
            college = get_data("college")

            # 如果沒有取得球員姓名，就跳過這一筆資料
            if not name:

                # 繼續讀取下一列球員資料
                continue

            # 將目前球員的所有資料加入 players 清單
            players.append([

                # 儲存球隊代碼
                team,

                # 儲存球員背號
                number,

                # 儲存球員姓名
                name,

                # 儲存球員位置
                position,

                # 儲存球員體重
                weight,

                # 儲存球員生日
                birthday,

                # 儲存球員 NBA 經驗年數
                experience,

                # 儲存球員就讀的大學
                college

            ])

            # 成功取得一位球員，計數器增加 1
            count += 1

        # 顯示目前球隊成功擷取的球員人數
        print(f"{team}：{count} 位球員")

    # 捕捉 requests 發生的網路請求錯誤
    except requests.exceptions.RequestException as e:

        # 顯示目前球隊的抓取失敗訊息及錯誤原因
        print(f"{team}：抓取失敗 - {e}")

    # 不論目前球隊抓取成功或失敗，都執行等待程序
    # 產生 3 到 5 秒之間的隨機等待時間
    time.sleep(random.uniform(3, 5))


# 開始檢查是否有成功抓取到球員資料
if players:

    # 開啟 CSV 檔案進行寫入
    # "w" 代表寫入模式
    # newline="" 避免 CSV 出現多餘空白列
    # encoding="utf-8-sig" 幫助 Excel 正確顯示中文
    with open(filename, "w", newline="", encoding="utf-8-sig") as file:

        # 建立 CSV 寫入物件
        writer = csv.writer(file)

        # 將欄位名稱寫入 CSV 第一列
        writer.writerow(headers)

        # 將所有球員資料逐列寫入 CSV
        writer.writerows(players)

    # 顯示總共成功抓取的球員人數
    print(f"\n總共抓取：{len(players)} 位球員")

    # 顯示 CSV 檔案實際儲存位置
    print(f"儲存檔案：{filename}")

# 如果 players 清單是空的，代表沒有成功抓取任何球員
else:

    # 顯示沒有抓取到資料的訊息
    print("\n沒有抓取到球員資料，未建立 CSV。")
