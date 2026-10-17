
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://www.atmovies.com.tw/movie/new/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers, timeout=20)
response.raise_for_status()
response.encoding = response.apparent_encoding

soup = BeautifulSoup(response.text, "html.parser")

# 找出電影資料
movies = soup.select("article")

if not movies:
    # 如果網站沒有使用 article 標籤，先列出頁面標題，
    # 再依實際 HTML 結構調整選取條件。
    print("找不到 article 標籤，請檢查網頁 HTML 結構。")
    print(soup.title.get_text(strip=True) if soup.title else "沒有網頁標題")
else:
    for movie in movies:
        title_tag = movie.select_one("h2, h3, a")
        if not title_tag:
            continue

        title = title_tag.get_text(" ", strip=True)
        link_tag = movie.select_one("a[href]")
        movie_url = (
            urljoin(url, link_tag["href"])
            if link_tag else "無網址"
        )

        content_tag = movie.select_one("p")
        content = (
            content_tag.get_text(" ", strip=True)
            if content_tag else "未找到內容"
        )

        text = movie.get_text(" ", strip=True)
        import re
        duration = re.search(r"片長[：:]\s*(\d+)\s*分", text)
        duration = duration.group(1) + " 分鐘" if duration else "未找到片長"

        print("電影標題：", title)
        print("電影內容：", content)
        print("片長：", duration)
        print("網址：", movie_url)
        print("-" * 50)
