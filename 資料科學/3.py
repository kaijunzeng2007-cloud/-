
import requests
import os
import csv
import io
from urllib.parse import quote

# 官方腸病毒統計 CSV 網址
url = "https://od.cdc.gov.tw/eic/NHI_EnteroviralInfection.csv"

# 固定儲存在 3.py 所在的資料夾
folder = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(
    folder, "NHI_EnteroviralInfection.csv"
)

# 檢查是否為腸病毒統計 CSV
required = {
    "年", "週", "就診類別", "年齡別",
    "縣市", "腸病毒健保就診人次",
    "健保就診總人次"
}

# 官方無法連線時，使用第三方備份來源
dataset = "健保門診及住院就診人次統計-腸病毒"
resource = "健保門診及住院就診人次統計.csv"

backup_url = (
    "https://doggy8088.github.io/cdc-data/data/"
    + quote(dataset) + "/" + quote(resource)
)

# 優先官方，失敗後使用備份
sources = [
    ("政府官方網站", url),
    ("第三方鏡像備份", backup_url)
]

success = False

for source_name, source_url in sources:
    try:
        response = requests.get(
            source_url,
            timeout=(6, 60)
        )
        response.raise_for_status()

        content = response.content

        if not content:
            raise ValueError("下載內容為空")

        # 檢查 CSV 格式
        text = content.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        header = next(reader, [])

        header = [item.strip() for item in header]

        if not required.issubset(set(header)):
            raise ValueError("CSV 欄位不符合腸病毒資料")

        if not any(reader):
            raise ValueError("CSV 沒有資料")

        # 加入 UTF-8 BOM，避免 Excel 中文亂碼
        if not content.startswith(b"\xef\xbb\xbf"):
            content = b"\xef\xbb\xbf" + content

        # 成功下載後才覆蓋原始檔案
        temp_file = filename + ".tmp"

        try:
            with open(temp_file, "wb") as f:
                f.write(content)

            os.replace(temp_file, filename)

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        print("CSV 資料已成功儲存至本地端")
        print("檔案名稱：NHI_EnteroviralInfection.csv")
        print("儲存位置：", filename)

        success = True
        break

    except (
        requests.RequestException,
        ValueError,
        UnicodeError,
        OSError
    ):
        continue

if not success:
    print("CSV 資料下載失敗，請檢查網路連線。")
