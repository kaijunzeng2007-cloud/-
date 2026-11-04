
import requests  # 匯入 requests 套件，用來連接網站及下載網路資料
import os  # 匯入 os 套件，用來處理資料夾及檔案路徑
import csv  # 匯入 csv 套件，用來讀取及檢查 CSV 資料
import io  # 匯入 io 套件，用來將文字轉換成可讀取的資料流
from urllib.parse import quote  # 匯入 quote，用來將中文網址轉換成 URL 編碼

# 官方腸病毒統計 CSV 網址
url = "https://od.cdc.gov.tw/eic/NHI_EnteroviralInfection.csv"

# 取得目前 Python 程式所在的資料夾
folder = os.path.dirname(os.path.abspath(__file__))

# 設定 CSV 檔案的完整儲存路徑
filename = os.path.join(
    folder, "NHI_EnteroviralInfection.csv"  # 組合資料夾路徑與檔案名稱
)

# 設定 CSV 必須包含的欄位名稱
required = {
    "年", "週", "就診類別", "年齡別",
    "縣市", "腸病毒健保就診人次",
    "健保就診總人次"
}

# 設定第三方備份網站的資料集名稱
dataset = "健保門診及住院就診人次統計-腸病毒"

# 設定第三方備份網站的 CSV 檔案名稱
resource = "健保門診及住院就診人次統計.csv"

# 建立第三方備份網站的完整網址
backup_url = (
    "https://doggy8088.github.io/cdc-data/data/"
    + quote(dataset) + "/" + quote(resource)  # 將中文名稱轉換成網址編碼
)

# 建立下載來源清單，優先使用政府官方網站
sources = [
    ("政府官方網站", url),  # 第一個下載來源
    ("第三方鏡像備份", backup_url)  # 第二個下載來源
]

success = False  # 設定下載成功狀態，預設為 False（尚未成功）

# 使用 for 迴圈，依序嘗試清單中的下載來源
for source_name, source_url in sources:

    try:  # 開始錯誤處理，避免下載失敗造成程式中斷

        # 使用 requests.get() 向網站發送下載請求
        response = requests.get(
            source_url,  # 指定目前要下載的網站網址
            timeout=(6, 60)  # 設定連線逾時 6 秒、讀取逾時 60 秒
        )

        response.raise_for_status()  # 檢查 HTTP 回應狀態，失敗時產生例外

        content = response.content  # 取得網站回傳的原始二進位資料

        if not content:  # 檢查下載的內容是否為空
            raise ValueError("下載內容為空")  # 如果沒有資料，就產生錯誤

        # 將下載的二進位資料解碼成 UTF-8 文字
        text = content.decode("utf-8-sig")

        # 使用 StringIO 將文字轉換成可以讀取的資料流
        reader = csv.reader(io.StringIO(text))

        # 讀取 CSV 第一列，取得欄位名稱
        header = next(reader, [])

        # 使用 strip() 移除每個欄位名稱前後的空白
        header = [item.strip() for item in header]

        # 檢查 CSV 是否包含所有必要欄位
        if not required.issubset(set(header)):

            # 如果缺少必要欄位，就產生錯誤
            raise ValueError("CSV 欄位不符合腸病毒資料")

        # 檢查 CSV 是否至少包含一筆資料
        if not any(reader):

            # 如果沒有任何資料，就產生錯誤
            raise ValueError("CSV 沒有資料")

        # 檢查是否已有 UTF-8 BOM，避免重複加入
        if not content.startswith(b"\xef\xbb\xbf"):

            # 在檔案開頭加入 UTF-8 BOM，幫助 Excel 正確顯示中文
            content = b"\xef\xbb\xbf" + content

        # 設定暫存檔案名稱，避免直接覆蓋原始檔案
        temp_file = filename + ".tmp"

        try:  # 開始暫存檔案的寫入程序

            # 以二進位寫入模式開啟暫存檔案
            with open(temp_file, "wb") as f:

                # 將下載的 CSV 資料寫入暫存檔案
                f.write(content)

            # 暫存檔案寫入成功後，再取代正式 CSV 檔案
            os.replace(temp_file, filename)

        finally:  # 不論成功或失敗，都執行以下清理程序

            # 檢查暫存檔案是否還存在
            if os.path.exists(temp_file):

                # 如果存在，就刪除暫存檔案
                os.remove(temp_file)

        # 顯示 CSV 資料成功儲存的訊息
        print("CSV 資料已成功儲存至本地端")

        # 顯示儲存的檔案名稱
        print("檔案名稱：NHI_EnteroviralInfection.csv")

        # 顯示 CSV 檔案實際儲存位置
        print("儲存位置：", filename)

        success = True  # 將下載成功狀態改為 True

        break  # 成功下載後跳出迴圈，不再嘗試其他來源

    # 捕捉網路、資料格式、編碼及檔案操作錯誤
    except (
        requests.RequestException,  # 網路連線或 HTTP 請求錯誤
        ValueError,  # CSV 資料內容或欄位不正確
        UnicodeError,  # 文字編碼錯誤
        OSError  # 檔案讀寫或作業系統錯誤
    ):

        continue  # 目前來源失敗，繼續嘗試下一個下載來源

# 檢查所有下載來源是否都已經嘗試過
if not success:

    # 如果全部失敗，就顯示下載失敗訊息
    print("CSV 資料下載失敗，請檢查網路連線。")
