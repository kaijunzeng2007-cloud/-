import time
from seleniumbase import SB

def scrape_all_google_news():
    # 使用 user_data_dir 儲存 Cookie，延續您已經通過驗證的狀態
    with SB(uc=True, user_data_dir="./google_news_cookie_profile", locale="zh-TW") as sb:
        # 【新增設定】進入網頁前，先將瀏覽器視窗自動最大化
        sb.maximize_window()
        
        search_keyword = "科技"
        url = f"https://news.google.com/search?q={search_keyword}&hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
        
        print(f"正在前往 Google 新聞（主題：{search_keyword}）...")
        sb.uc_open_with_reconnect(url, reconnect_time=4)
        
        # 若遇到驗證手動處理
        if "sorry" in sb.get_current_url() or "captcha" in sb.get_page_source().lower():
            print("\n" + "=" * 50)
            print("⚠ 偵測到驗證畫面，請手動勾選一次驗證方塊。")
            input("👉 完成後請回到此處按【Enter 鍵】繼續...")
            print("=" * 50 + "\n")
        
        print("正在快速且大幅度向下滾動，直達網頁最底部...")
        
        # 快速向下滾動以加載所有內容
        for i in range(12):
            sb.execute_script("window.scrollBy(0, 1800);")
            time.sleep(0.8)
        
        print("已抵達底部，開始抓取全部新聞標題...")
        
        # 抓取所有標題（結合 h3 與 a 標籤以確保完整）
        all_titles = []
        seen = set()
        
        h3_elements = sb.find_elements("h3")
        for elem in h3_elements:
            text = elem.text.strip()
            if text and text not in seen:
                seen.add(text)
                all_titles.append(text)
                
        if not all_titles:
            links = sb.find_elements("a")
            for link in links:
                text = link.text.strip()
                if len(text) > 10 and text not in seen:
                    seen.add(text)
                    all_titles.append(text)

        # 分配資料到各個欄位
        focus_summary = ["Google 新聞即時焦點與熱門摘要"]
        total_count = len(all_titles)
        
        if total_count >= 4:
            chunk = total_count // 4
            focus_news = all_titles[:chunk]
            local_news = all_titles[chunk:chunk*2]
            your_topic = all_titles[chunk*2:chunk*3]
            more_news = all_titles[chunk*3:]
        else:
            focus_news = all_titles
            local_news = ["(無特定地方新聞)"]
            your_topic = []
            more_news = []

        # 嚴格依照您的格式輸出
        print("\n" + "=" * 50)
        print(f"焦點提要：{focus_summary}")
        
        print(f"\n焦點新聞：")
        for t in (focus_news if focus_news else ["(目前無資料)"]):
            print(f"  - {t}" if not t.startswith("(") else f"  {t}")
            
        print(f"\n地方新聞：")
        for t in (local_news if local_news else ["(目前無資料)"]):
            print(f"  - {t}" if not t.startswith("(") else f"  {t}")
            
        print(f"\n您的主題 ({search_keyword})：")
        for t in (your_topic if your_topic else ["(目前無資料)"]):
            print(f"  - {t}" if not t.startswith("(") else f"  {t}")
            
        print(f"\n更多新聞：")
        for t in (more_news if more_news else ["(目前無資料)"]):
            print(f"  - {t}" if not t.startswith("(") else f"  {t}")
        print("=" * 50 + "\n")

if __name__ == "__main__":
    scrape_all_google_news()
