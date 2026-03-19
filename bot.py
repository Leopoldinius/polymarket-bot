import requests
import time
import urllib3
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🔑 Встав свій токен та чат
TELEGRAM_TOKEN = "8667045124:AAGS4HceBcGJUAkGAZpqXAWUYmQAtJNzvEo"
CHAT_ID = "598513173"

# Зберігаємо ID вже побачених ринків
seen_markets = set()

# Скільки днів вважаємо ринок "новим"
NEW_DAYS = 3

# User-Agent для запитів до Polymarket
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"}

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
    limit = 100

    while True:
        url = f"https://gamma-api.polymarket.com/markets?tag_slug=crypto&limit={limit}&offset={offset}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            try:
                data = response.json()
            except Exception as e:
                print("❌ Не вдалося прочитати JSON:", e)
                break

            if not data:
                break

            # Відбираємо тільки відкриті ринки
            open_markets = [m for m in data if m.get("status") == "open"]
            all_markets.extend(open_markets)

            offset += limit

        except Exception as e:
            print("❌ Помилка get_markets:", e)
            break

    print(f"📦 Завантажено {len(all_markets)} відкритих ринків")
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

            # Безпечна обробка timestamp
            try:
                created_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                try:
                    created_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                except Exception as e:
                    print("❌ Помилка конвертації timestamp:", created_at, e)
                    continue

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

# 🚀 Старт
print("🚀 Bot started...")
print("⏳ Перший запит до API...")

# Перше завантаження без спаму
try:
    initial_markets = get_markets()
except Exception as e:
    initial_markets = []
    print("❌ Помилка першого завантаження:", e)

now = datetime.utcnow()
threshold = now - timedelta(days=NEW_DAYS)
for m in initial_markets:
    created_at = m.get("createdAt")
    if m.get("id") and created_at:
        try:
            created_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            try:
                created_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                continue
        if created_dt >= threshold:
            seen_markets.add(m["id"])

print(f"📦 Ініціалізовано: {len(seen_markets)} ринків (нових за {NEW_DAYS} днів)")

send_message(f"✅ Бот запущений і працює. Слідкує за ринками за останні {NEW_DAYS} днів")

# 🔁 Цикл перевірки кожну хвилину
while True:
    try:
        check_markets()
    except Exception as e:
        print("❌ Помилка в циклі:", e)
    time.sleep(60)