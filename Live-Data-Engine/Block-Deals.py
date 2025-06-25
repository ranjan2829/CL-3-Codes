from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)

url = "https://www.nseindia.com/market-data/equity-block-deals"
driver.get(url)
time.sleep(5)
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
table = soup.find('table', {'id': 'equityBlockDeals'})
if not table:
    print("Block deals table not found!")
    driver.quit()
    exit()

rows = table.find_all('tr')[1:]

for row in rows:
    cols = row.find_all('td')
    if len(cols) < 6:
        continue
    symbol = cols[0].text.strip()
    quantity = cols[1].text.strip()
    price = cols[2].text.strip()
    deal_date = cols[3].text.strip()
    deal_time = cols[4].text.strip()
    client_name = cols[5].text.strip()

    print(f"{symbol} | Qty: {quantity} | Price: {price} | Date: {deal_date} | Time: {deal_time} | Client: {client_name}")

driver.quit()
