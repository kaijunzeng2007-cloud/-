from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Edge()
driver.implicitly_wait(10)

# 先進入 PTT 網站
driver.get("https://www.ptt.cc/")

# 輸入 Cookie
cookie = {
    "name": "over18",
    "value": "1"
}

driver.add_cookie(cookie)

# Cookie 已經存在，再進入八卦版
driver.get("https://www.ptt.cc/bbs/Gossiping/index.html")

print("----------------------------------------")
print(driver.title)
print("----------------------------------------")

# 抓文章列表
articles = driver.find_elements(By.CSS_SELECTOR, "div.r-ent")

for article in articles:

    title = article.find_elements(By.CSS_SELECTOR, "div.title a")

    if not title:
        continue

    print("網址：", title[0].get_attribute("href"))
    print("標題：", title[0].text)

    author = article.find_element(
        By.CSS_SELECTOR,
        "div.author"
    ).text

    print("作者：", author)

    print("----------------------------------------")

driver.quit()