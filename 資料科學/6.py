from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import csv
import time


# ========================================
# 1. 球隊
# ========================================

teams = ["CLE", "HOU", "GSW"]

url_template = "https://www.basketball-reference.com/teams/{}/2024.html"


# ========================================
# 2. Selenium 設定
# ========================================

options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)

players = []


try:

    # ========================================
    # 3. 抓取三支球隊
    # ========================================

    for team in teams:

        url = url_template.format(team)

        print("\n========================================")
        print(f"正在抓取：{team}")
        print(url)
        print("========================================")

        driver.get(url)

        time.sleep(5)

        # 取得 HTML
        html = driver.page_source

        # BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")


        # ========================================
        # 4. 找 Roster 表格
        # ========================================

        table = soup.find("table", id="roster")

        if table is None:
            print(f"{team} 找不到 roster 表格")
            continue


        tbody = table.find("tbody")

        if tbody is None:
            print(f"{team} 找不到 tbody")
            continue


        # ========================================
        # 5. 讀取每一位球員
        # ========================================

        team_count = 0

        for row in tbody.find_all("tr"):

            cells = row.find_all(["th", "td"])

            if not cells:
                continue


            # -------------------------------
            # 讀取 data-stat
            # -------------------------------

            data = {}

            for cell in cells:

                stat = cell.get("data-stat")

                if stat:
                    data[stat] = cell.get_text(
                        " ",
                        strip=True
                    )


            # ========================================
            # 6. 建立球員資料
            # ========================================

            player = {

                "球隊": team,

                "背號": data.get(
                    "number",
                    ""
                ),

                "姓名": data.get(
                    "player",
                    ""
                ),

                "位置": data.get(
                    "pos",
                    ""
                ),

                "體重": data.get(
                    "weight",
                    ""
                ),

                "生日": data.get(
                    "birth_date",
                    ""
                ),

                "經驗": data.get(
                    "experience",
                    ""
                ),

                "大學": data.get(
                    "college_name",
                    ""
                )
            }


            # ========================================
            # 7. 印出資料
            # ========================================

            if player["姓名"]:

                # 加入 players
                players.append(player)

                team_count += 1


                # ★★★ 印出 8 個欄位 ★★★

                print(
                    f"球隊：{player['球隊']}"
                )

                print(
                    f"背號：{player['背號']}"
                )

                print(
                    f"姓名：{player['姓名']}"
                )

                print(
                    f"位置：{player['位置']}"
                )

                print(
                    f"體重：{player['體重']}"
                )

                print(
                    f"生日：{player['生日']}"
                )

                print(
                    f"經驗：{player['經驗']}"
                )

                print(
                    f"大學：{player['大學']}"
                )

                print("----------------------------------------")


        print(
            f"{team} 完成，共 {team_count} 位球員"
        )

        time.sleep(3)


finally:

    driver.quit()


# ========================================
# 8. 寫入 CSV
# ========================================

filename = "players.csv"

fieldnames = [
    "球隊",
    "背號",
    "姓名",
    "位置",
    "體重",
    "生日",
    "經驗",
    "大學"
]


with open(
    filename,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(players)


# ========================================
# 9. 完成
# ========================================

print()
print("========================================")
print("完成！")
print("========================================")

print(f"總共抓到：{len(players)} 位球員")
print(f"CSV 檔案：{filename}")