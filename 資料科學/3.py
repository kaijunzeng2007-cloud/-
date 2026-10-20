
import requests
import os
import warnings
import urllib3

# 官方腸病毒健保就診統計 CSV 網址
url = "https://od.cdc.gov.tw/eic/NHI_EnteroviralInfection.csv"

# 固定儲存在 3.py 所在的資料夾
folder = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(folder, "NHI_EnteroviralInfection.csv")

try:
    print("正在連接政府資料網站...")
    
    # 正常情況先驗證 SSL 憑證
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

    except requests.exceptions.SSLError:
        # 此官方網址目前遇到憑證驗證問題時的暫時替代方式。
        # 注意：verify=False 會略過 SSL 憑證驗證，
        # 只應用於確認過的固定官方網址。
        print("SSL 憑證驗證失敗，改用暫時替代方式下載...")
        urllib3.disable_warnings(
            urllib3.exceptions.InsecureRequestWarning
        )
        response = requests.get(
            url,
            timeout=60,
            verify=False
        )
        response.raise_for_status()

    # 確認回應不是空的
    if not response.content:
        raise ValueError("下載內容是空的。")

    # 確認內容看起來像 CSV，而不是錯誤網頁
    content = response.content
    preview = content[:1000].lstrip().lower()

    if b"<html" in preview or b"<!doctype html" in preview:
        raise ValueError("網站回傳的是 HTML，不是 CSV 資料。")

    # 如果原始檔案是 UTF-8，加入 BOM 方便 Excel 辨識中文
    if not content.startswith(b"\xef\xbb\xbf"):
        try:
            content.decode("utf-8")
            content = b"\xef\xbb\xbf" + content
        except UnicodeDecodeError:
            print("提醒：原始內容不是標準 UTF-8，保留原始位元組。")

    # 每次執行都重新寫入最新下載內容
    with open(filename, "wb") as f:
        f.write(content)

    print("下載成功！")
    print("HTTP 狀態碼：", response.status_code)
    print("檔案名稱：NHI_EnteroviralInfection.csv")
    print("儲存位置：", filename)
    print("檔案大小：", len(content), "bytes")

except (requests.RequestException, ValueError, OSError) as e:
    print("資料下載失敗：", e)
