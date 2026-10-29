
import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import random

# 設定球隊
TEAMS = ["CLE", "HOU", "GSW"]

# 設定網址
URL = "https://www.basketball-reference.com/teams/{0}/2024.html"

# 儲存路徑（與 Python 程式相同資料夾）
folder = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(folder, "players.csv")

# CSV 標頭
headers = ["球隊", "背號", "姓名", "位置", "體重", "生日", "經驗", "大學"]

# 儲存所有球員
players = []

# HTTP 標頭
http_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

session = requests.Session()
session.headers.update(http_headers)

for team in TEAMS:
    try:
        response = session.get(URL.format(team), timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 找到球員名單表格
        table = soup.find("table", id="roster")

        if table is None:
            print(f"{team}：找不到球員名單")
            continue

        tbody = table.find("tbody")

        if tbody is None:
            print(f"{team}：找不到球員資料")
            continue

        count = 0

        for tr in tbody.find_all("tr"):
            # 依照 data-stat 欄位抓取資料
            def get_data(stat):
                cell = tr.find(["th", "td"], attrs={"data-stat": stat})
                return cell.get_text(" ", strip=True) if cell else ""

            number = get_data("number")
            name = get_data("player")
            position = get_data("pos")
            weight = get_data("weight")
            birthday = get_data("birth_date")
            experience = get_data("years_experience")
            college = get_data("college")

            if not name:
                continue

            players.append([
                team,
                number,
                name,
                position,
                weight,
                birthday,
                experience,
                college
            ])

            count += 1

        print(f"{team}：{count} 位球員")

    except requests.exceptions.RequestException as e:
        print(f"{team}：抓取失敗 - {e}")

    # 避免短時間內連續發送請求
    time.sleep(random.uniform(3, 5))

# 儲存 CSV
if players:
    with open(filename, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(players)

    print(f"\n總共抓取：{len(players)} 位球員")
    print(f"儲存檔案：{filename}")
else:
    print("\n沒有抓取到球員資料，未建立 CSV。")
