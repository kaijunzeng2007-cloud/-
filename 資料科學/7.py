
import requests
import csv

url = "https://www.googleapis.com/books/v1/volumes"

# 請將這裡換成你自己的 Google Cloud API Key
API_KEY = "AIzaSyD4uttVu4RYvDpyTkDB6p75-nGHFcxOLzU"

url_params = {
    'q': 'Python',
    'maxResults': 10,
    'projection': 'lite',
    'key': API_KEY
}

# 將兩頁資料存入同一個 CSV 檔案
with open('pythonbook.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)

    # 寫入標題列
    writer.writerow(['書名', '作者', '出版社', '出版日期'])

    # 抓取兩頁
    for page in range(2):
        # 設定分頁起始位置
        url_params['startIndex'] = page * 10

        try:
            r = requests.get(url, params=url_params, timeout=20)

            print(f'第 {page + 1} 頁，HTTP 狀態碼：{r.status_code}')

            if r.status_code != 200:
                print('API 查詢失敗：')
                print(r.text)
                break

            data = r.json()

            # 取得書籍資料
            books = data.get('items', [])

            if not books:
                print('這一頁沒有書籍資料。')
                break

            for book in books:
                info = book.get('volumeInfo', {})

                title = info.get('title', '')
                authors = ', '.join(info.get('authors', []))
                publisher = info.get('publisher', '')
                published_date = info.get('publishedDate', '')

                writer.writerow([
                    title,
                    authors,
                    publisher,
                    published_date
                ])

                print('書名：', title)

            print(f'第 {page + 1} 頁完成，共取得 {len(books)} 本書。')

        except requests.exceptions.RequestException as e:
            print('網路連線錯誤：', e)
            break

print('程式執行結束，資料已寫入 pythonbook.csv（若 API 查詢成功）。')
