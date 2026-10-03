import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# 設定搜尋關鍵字與獨立的 Chrome 使用者資料夾路徑（避免與日常瀏覽器衝突）
KEYWORD = "科技"
PROFILE = r"C:\selenium_google_news_profile"
NEWS_URL = f"https://news.google.com/search?q={KEYWORD}&hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"

def clean_titles(titles):
    """資料清洗函式：去除標題多餘空白、過濾空字串並過濾重複項目"""
    result = []
    for title in titles:
        title = " ".join(title.split()).strip()
        if not title:
            continue
        if title not in result:
            result.append(title)
    return result

def wait_for_verification(driver):
    """機器人驗證檢測：若偵測到 Google 驗證畫面，暫停並讓使用者手動處理"""
    source = driver.page_source.lower()
    if any(k in source for k in ["captcha", "recaptcha", "i'm not a robot", "unusual traffic"]):
        print("\n" + "=" * 50)
        print("⚠ 偵測到 Google 驗證畫面！")
        input("👉 請在瀏覽器中手動完成驗證，完成後回到此處按【Enter 鍵】繼續...")
        print("=" * 50 + "\n")

def main():
    # 確保隔離的 Profile 目錄存在
    os.makedirs(PROFILE, exist_ok=True)
    
    # 【關鍵機制】自動清除上次異常崩潰所留下的 SingletonLock 檔案，防止啟動卡死
    lock_file = os.path.join(PROFILE, "SingletonLock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except:
            pass

    # 設定 Chrome 瀏覽器選項
    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE}")
    options.add_argument("--lang=zh-TW")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # 【關鍵設定】強制啟用圖片載入（設定為 1 代表允許載入圖片），確保瀏覽器完整渲染圖檔
    prefs = {"profile.managed_default_content_settings.images": 1}
    options.add_experimental_option("prefs", prefs)
    
    # 啟動瀏覽器
    driver = webdriver.Chrome(options=options)
    
    try:
        # 視窗最大化並前往 Google 新聞頁面
        driver.maximize_window()
        driver.get(NEWS_URL)
        
        time.sleep(2)
        wait_for_verification(driver)
        
        # 【平滑慢速捲動】透過迴圈一步步往下滾動，直到網頁高度不再增加（真正滾到底部）
        last_y = -1
        while True:
            driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(0.8)  # 每次滾動暫停 0.8 秒，速度適中且能讓內容加載
            current_y = driver.execute_script("return window.pageYOffset;")
            if current_y == last_y:
                break
            last_y = current_y
            
        # 捲動到底後，額外等待 3 秒讓網頁上的圖片與縮圖完整渲染顯示
        print("正在等待圖片與頁面完全載入...")
        time.sleep(3)
        
        # 抓取新聞標題元素
        all_titles = []
        h3_elements = driver.find_elements(By.TAG_NAME, "h3")
        for elem in h3_elements:
            all_titles.append(elem.text)
            
        # 若 h3 數量不足，則透過超連結標籤（a 標籤）作為備用補充
        if len(all_titles) < 10:
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                text = link.text.strip()
                if len(text) > 10:
                    all_titles.append(text)
                    
        # 清洗與過濾重複標題
        cleaned_all = clean_titles(all_titles)
        
        # 將抓取到的新聞平均分配到四個欄位分類中
        total_count = len(cleaned_all)
        if total_count >= 4:
            chunk = total_count // 4
            focus_news = cleaned_all[:chunk]
            local_news = cleaned_all[chunk:chunk*2]
            topic_news = cleaned_all[chunk*2:chunk*3]
            more_news = cleaned_all[chunk*3:]
        else:
            focus_news = cleaned_all
            local_news = []
            topic_news = []
            more_news = []

        # 將分類結果以整潔的純文字格式輸出至終端機
        print("\n" + "=" * 50)
        
        print(f"焦點新聞 ({len(focus_news)} 筆)：")
        for t in (focus_news if focus_news else ["(目前無資料)"]):
            print(f"  - {t}" if not t.startswith("(") else f"  {t}")
            
        print(f"\n地方新聞 ({len(local_news)} 筆)：")
        for t in (local_news if local_news else ["(目前無資料)"]):
            print(f"  - {t}" if not t.startswith("(") else f"  {t}")
            
        print(f"\n您的主題 ({KEYWORD}) ({len(topic_news)} 筆)：")
        for t in (topic_news if topic_news else ["(目前無資料)"]):
            print(f"  - {t}" if not t.startswith("(") else f"  {t}")
            
        print(f"\n更多新聞 ({len(more_news)} 筆)：")
        for t in (more_news if more_news else ["(目前無資料)"]):
            print(f"  - {t}" if not t.startswith("(") else f"  {t}")
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"❌ 執行過程中發生錯誤：{e}")
    finally:
        # 確保程式結束時自動關閉瀏覽器，釋放資源
        time.sleep(1)
        driver.quit()

if __name__ == "__main__":
    main()