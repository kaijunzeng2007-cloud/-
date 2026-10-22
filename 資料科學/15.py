
import csv
import os
import time
from urllib.parse import parse_qs, quote, urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

KEYWORD = "xpath"
PROFILE = r"C:\selenium_xpath_profile"
CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xpath.csv")
SEARCH_URL = f"https://www.google.com/search?q={quote(KEYWORD)}&hl=zh-TW&gl=TW"


def text_clean(value):
    return " ".join((value or "").split())


# Google 驗證：人工完成後自動繼續
def wait_captcha(driver):
    def challenged(d):
        return "/sorry/" in d.current_url or bool(
            d.find_elements(By.ID, "captcha-form")
        )

    if challenged(driver):
        print("請在 Chrome 完成 Google 驗證，程式會自動繼續。")
        WebDriverWait(driver, 600, poll_frequency=2).until(
            lambda d: not challenged(d)
        )


# 偵測 AI 摘要
def ai_label(driver):
    return driver.execute_script(r"""
        const ok = e => e && e.getClientRects().length > 0;
        const re = /AI\s*(摘要|Overview)/i;
        const walker = document.createTreeWalker(
            document.body, NodeFilter.SHOW_TEXT
        );
        let n;

        while ((n = walker.nextNode())) {
            const s = (n.nodeValue || '')
                .replace(/\s+/g, ' ').trim();

            if (s.length <= 35 && re.test(s) && ok(n.parentElement))
                return n.parentElement;
        }

        return [...document.querySelectorAll('span,div,h2,h3,strong')]
            .find(e => ok(e) && (e.innerText || '').length <= 35 &&
                re.test(e.innerText || '')) || null;
    """)


# 取得 AI 摘要內容
def ai_text(driver):
    label = ai_label(driver)

    if not label:
        return ""

    return driver.execute_script("""
        let e = arguments[0], best = '';

        for (let i = 0; e && i < 16; i++, e = e.parentElement) {
            if (e === document.body ||
                ['search', 'rso'].includes(e.id) ||
                e.tagName === 'MAIN') break;

            const s = (e.innerText || '').trim();
            const count = e.querySelectorAll('a[href] h3').length;

            if (count > 3) break;

            if (s.length > 90 && s.length < 40000)
                best = s;
        }

        return best;
    """, label) or ""


# 點擊 AI 摘要的「顯示更多」
def expand_ai(driver):
    label = ai_label(driver)

    if not label:
        return

    button = driver.execute_script(r"""
        const y0 = arguments[0].getBoundingClientRect().top + scrollY;
        const re = /^(顯示更多|查看更多|Show more|Read more)\s*[⌄˅∨▼]?$/i;
        const walker = document.createTreeWalker(
            document.body, NodeFilter.SHOW_TEXT
        );

        const choices = [];
        let n;

        while ((n = walker.nextNode())) {
            if (!re.test((n.nodeValue || '').replace(/\s+/g, ' ').trim()))
                continue;

            const e = n.parentElement.closest(
                'button,[role="button"]'
            ) || n.parentElement;

            if (!e.getClientRects().length || e.closest('a[href]'))
                continue;

            const y = e.getBoundingClientRect().top + scrollY;

            if (y >= y0 - 20 && y <= y0 + 2500)
                choices.push({e, y});
        }

        choices.sort((a, b) => a.y - b.y);

        return choices.length ? choices[0].e : null;
    """, label)

    if not button:
        return

    before = len(ai_text(driver))

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'})", button
    )

    try:
        button.click()
    except WebDriverException:
        driver.execute_script("arguments[0].click()", button)

    try:
        WebDriverWait(driver, 8).until(
            lambda d: len(ai_text(d)) > before + 15
        )
    except TimeoutException:
        pass


# 清理搜尋結果網址
def clean_url(url):
    parsed = urlparse(url or "")

    if parsed.scheme not in ("http", "https"):
        return ""

    if parsed.hostname in (
        "google.com", "www.google.com",
        "google.com.tw", "www.google.com.tw"
    ):
        if parsed.path == "/url":
            args = parse_qs(parsed.query)
            return (args.get("q") or args.get("url") or [""])[0]

        return url if parsed.path == "/goto" else ""

    return url.split("#", 1)[0]


# 抓取第一頁搜尋結果
def collect(driver, results):
    headings = driver.find_elements(
        By.CSS_SELECTOR, "#search h3, #rso h3, main h3"
    )

    for h in headings:
        try:
            title = text_clean(h.text)

            link = h.find_element(
                By.XPATH, "./ancestor::a[@href][1]"
            )

            url = clean_url(link.get_attribute("href"))

            if not title or not url or url in results:
                continue

            summary = ""

            try:
                block = h.find_element(
                    By.XPATH,
                    "./ancestor::div[contains(@class,'MjjYud')][1]"
                )

                for e in block.find_elements(
                    By.CSS_SELECTOR,
                    ".VwiC3b, .yXK7lf, [data-sncf]"
                ):
                    s = text_clean(e.text)

                    if s and s != title:
                        summary = s[:1500]
                        break

            except WebDriverException:
                pass

            results[url] = (title, url, summary)

        except WebDriverException:
            continue


# 自動捲動第一頁
def scroll_first_page(driver, results):
    same = 0

    for _ in range(45):
        wait_captcha(driver)
        collect(driver, results)

        before = driver.execute_script(
            "return [scrollY, document.documentElement.scrollHeight]"
        )

        driver.execute_script("scrollBy(0, 700)")
        time.sleep(0.55)

        after = driver.execute_script(
            "return [scrollY, document.documentElement.scrollHeight]"
        )

        same = same + 1 if before == after else 0

        if same >= 3:
            break

    collect(driver, results)


# 避免 Excel 將文字誤判為公式
def safe(value):
    value = str(value or "")

    if value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value

    return value


# 主程式
def main():
    os.makedirs(PROFILE, exist_ok=True)

    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE}")
    options.add_argument("--lang=zh-TW")
    options.add_argument("--start-maximized")

    driver = None
    results, ai, page_text = {}, "", ""

    try:
        # 啟動 Chrome 並最大化
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()

        # 開啟 Google
        driver.get("https://www.google.com/?hl=zh-TW")
        wait_captcha(driver)

        # 搜尋 xpath
        try:
            search = WebDriverWait(driver, 12).until(
                lambda d: d.find_element(By.NAME, "q")
            )

            search.clear()
            search.send_keys(KEYWORD, Keys.ENTER)

        except (TimeoutException, WebDriverException):
            driver.get(SEARCH_URL)

        wait_captcha(driver)

        # 等待搜尋結果載入
        WebDriverWait(driver, 20).until(
            lambda d: bool(d.find_elements(
                By.CSS_SELECTOR, "#search h3, #rso h3, main h3"
            )) or ai_label(d)
        )

        # 等待 AI 摘要載入
        try:
            WebDriverWait(driver, 12).until(
                lambda d: ai_label(d)
            )
        except TimeoutException:
            pass

        # 展開 AI 摘要並擷取完整可取得的文字
        ai = ai_text(driver)
        expand_ai(driver)
        ai = max(ai, ai_text(driver), key=len)

        # 捲動第一頁並抓取搜尋結果
        scroll_first_page(driver, results)

        # 再次確認 AI 摘要內容
        ai = max(ai, ai_text(driver), key=len)

        # 備份第一頁可見文字
        page_text = driver.execute_script("""
            const area = document.querySelector('#search') ||
                         document.querySelector('#rso') ||
                         document.querySelector('main');

            return area ? area.innerText : '';
        """)

    except Exception as e:
        print(f"執行錯誤：{e}")

    finally:
        if driver:
            driver.quit()

    # 整理全部抓取資料
    rows = []

    if ai:
        rows.append(("AI 摘要", "Google AI 摘要", "", ai))

    rows.extend(
        ("搜尋結果", *item)
        for item in results.values()
    )

    if page_text:
        rows.append((
            "本頁文字備份",
            "Google 第一頁可見文字",
            "",
            page_text
        ))

    if not rows:
        print("沒有取得資料，保留原本的 xpath.csv。")
        return

    # 儲存所有資料至 CSV
    with open(
        CSV_FILE, "w", newline="", encoding="utf-8-sig"
    ) as f:
        writer = csv.writer(f)

        writer.writerow([
            "編號", "類型", "標題", "網址", "摘要或完整內容"
        ])

        for i, row in enumerate(rows, 1):
            writer.writerow([i, *(safe(v) for v in row)])

    # 終端機詳細列印全部資料
    print(f"搜尋關鍵字：{KEYWORD}")

    for i, (kind, title, url, content) in enumerate(rows, 1):
        print(f"\n第 {i} 筆（{kind}）")
        print(f"標題：{title}")

        if url:
            print(f"網址：{url}")

        print(f"內容：{content or '（未取得）'}")

    print(f"\n第一頁搜尋結果：{len(results)} 筆")
    print(f"全部儲存資料：{len(rows)} 筆")
    print(f"CSV 已儲存：{CSV_FILE}")


if __name__ == "__main__":
    main()
