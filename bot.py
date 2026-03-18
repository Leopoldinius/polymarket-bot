import requests
import schedule
import time
import urllib3

# Вимикаємо SSL попередження
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🔑 ВСТАВ СВОЇ ДАНІ
TELEGRAM_TOKEN = "8667045124:AAGS4HceBcGJUAkGAZpqXAWUYmQAtJNzvEo"
CHAT_ID = "598513173"

URL = "https://gamma-api.polymarket.com/markets?tag_slug=crypto"

known_markets = None  # щоб не спамити старими


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(url, data=data, verify=False)


def check_markets():
    global known_markets

    try:
        response = requests.get(URL, verify=False)

        if response.status_code != 200 or response.text.strip() == "":
            print("❌ API не відповідає")
            return

        markets = response.json()
        current_markets = set()

        for market in markets:
            title = market.get("question")
            if not title:
                continue

            current_markets.add(title)

            # якщо перший запуск — просто запам'ятати і не слати
            if known_markets is None:
                continue

            if title not in known_markets:
                liquidity = float(market.get("liquidity", 0) or 0)
                volume = float(market.get("volume", 0) or 0)
                link = f"https://polymarket.com{market.get('path', '')}"

                message = (
                    f"🆕 <b>{title}</b>\n\n"
                    f"💰 Ліквідність: ${liquidity:,.0f}\n"
                    f"📊 Обсяг: ${volume:,.0f}\n"
                    f"🔗 <a href='{link}'>Відкрити ринок</a>"
                )

                send_message(message)

        # ініціалізація бази (після першого запуску)
        if known_markets is None:
            known_markets = current_markets
            print("✅ База ініціалізована (старі ринки пропущені)")
        else:
            known_markets = current_markets

        print("🔄 Перевірка завершена")

    except Exception as e:
        print("Error:", e)


# ⏱ перевірка кожну 1 хвилину
schedule.every(1).minutes.do(check_markets)

print("🚀 Bot started...")

# перший запуск
check_markets()

while True:
    schedule.run_pending()
    time.sleep(1)