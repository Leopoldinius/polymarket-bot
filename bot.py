import requests
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🔑 ВСТАВ НОВИЙ ТОКЕН!
TELEGRAM_TOKEN = "8667045124:AAGS4HceBcGJUAkGAZpqXAWUYmQAtJNzvEo"
CHAT_ID = "598513173"

URL = "https://gamma-api.polymarket.com/markets?tag_slug=crypto"

# 🔒 тепер зберігаємо ID ринків (не назви!)
seen_markets = set()


def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("❌ Telegram error:", e)


def get_markets():
    try:
        response = requests.get(URL, timeout=10)

        if response.status_code != 200:
            print("❌ API статус:", response.status_code)
            return []

        return response.json()

    except Exception as e:
        print("❌ API error:", e)
        return []


def check_markets():
    global seen_markets

    markets = get_markets()
    if not markets:
        print("⚠️ Немає даних")
        return

    print(f"🔎 Отримано ринків: {len(markets)}")

    new_found = 0

    for market in markets:
        market_id = market.get("id")
        title = market.get("question")

        if not market_id or not title:
            continue

        # якщо новий
        if market_id not in seen_markets:
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

            print("🆕 Новий ринок:", title)
            new_found += 1

        seen_markets.add(market_id)

    print(f"✅ Нових: {new_found}")
    print("------")


# 🚀 старт
print("🚀 Bot started...")

# перше завантаження (без спаму)
initial_markets = get_markets()
for m in initial_markets:
    if m.get("id"):
        seen_markets.add(m["id"])

print(f"📦 Ініціалізовано: {len(seen_markets)} ринків")

# тест повідомлення
send_message("✅ Бот запущений і працює")

# 🔁 цикл
while True:
    check_markets()
    time.sleep(60)  # 1 хвилина