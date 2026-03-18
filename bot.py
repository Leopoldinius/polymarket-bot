import requests
import time
import schedule
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = "8667045124:AAGS4HceBcGJUAkGAZpqXAWUYmQAtJNzvEo"
CHAT_ID = "598513173"

URL = "https://gamma-api.polymarket.com/markets?tag_slug=crypto"

known_markets = set()

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=data)

def check_markets():
    global known_markets

    try:
        response = requests.get(URL)
        markets = response.json()

        current_markets = set()

        for market in markets:
            title = market["question"]
            current_markets.add(title)

            if title not in known_markets:
                send_message(f"🆕 Новий ринок:\n{title}")

        known_markets = current_markets

    except Exception as e:
        print("Error:", e)

schedule.every(2).minutes.do(check_markets)

print("Bot started...")

check_markets()

while True:
    schedule.run_pending()
    time.sleep(1)