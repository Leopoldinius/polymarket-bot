import requests
import time
import urllib3
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🔑 ВСТАВ НОВИЙ ТОКЕН!
TELEGRAM_TOKEN = "8667045124:AAGS4HceBcGJUAkGAZpqXAWUYmQAtJNzvEo"
CHAT_ID = "598513173"

# 🔒 для збереження ID вже побачених ринків
seen_markets = set()

# 🔒 скільки днів вважаємо ринок "новим"
NEW_DAYS = 3  # змінили на 3 дні

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
    all_markets = []
    offset = 0
    limit = 100  # швидко і стабільно

    while True:
        url = f"https://gamma-api.polymarket.com/markets?tag_slug=crypto&limit={limit}&offset={offset}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print("❌ API статус:", response.status_code)
                break

            data = response.json()
            if not data:
                break

            # відбираємо тільки відкриті ринки
            open_markets = [m for m in data if m.get("status") == "open"]
            all_markets.extend(open_markets)

            offset += limit

        except Exception as e:
            print("❌ API error:", e)
            break

    return all_markets

def check_markets():
    global seen_markets

    try:
        markets = get_markets()
        if not markets:
            print("⚠️ Немає даних")
            return

        new_found = 0
        now = datetime.utcnow()
        threshold = now - timedelta(days=NEW_DAYS)

        for market in markets:
            market_id = market.get("id")
            title = market.get("question")
            created_at = market.get("createdAt")

            if not market_id or not title or not created_at:
                continue

            try:
                created_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                created_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")

            if created_dt < threshold:
                continue

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

        print(f"✅ Нових ринків за останні {NEW_DAYS} днів: {new_found}")
        print("------")

    except Exception as e:
        print("❌ Помилка в check_markets:", e)

# 🚀 старт
print("🚀 Bot started...")
print("⏳ Перший запит до API...")

# перше завантаження (без спаму)
initial_markets = get_markets()
now = datetime.utcnow()
threshold = now - timedelta(days=NEW_DAYS)
for m in initial_markets:
    created_at = m.get("createdAt")
    if m.get("id") and created_at:
        try:
            created_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            created_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
        if created_dt >= threshold:
            seen_markets.add(m["id"])

print(f"📦 Ініціалізовано: {len(seen_markets)} ринків (нових за {NEW_DAYS} днів)")

send_message(f"✅ Бот запущений і працює. Слідкує за ринками за останні {NEW_DAYS} днів")

# 🔁 цикл перевірки кожну хвилину
while True:
    try:
        check_markets()
    except Exception as e:
        print("❌ Помилка в циклі:", e)
    time.sleep(60)