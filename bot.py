import requests
import time
from datetime import datetime, timedelta, timezone

# 🔑 Встав свій токен та чат
TELEGRAM_TOKEN = "8667045124:AAGS4HceBcGJUAkGAZpqXAWUYmQAtJNzvEo"
CHAT_ID = "598513173"

# User-Agent для API
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"}

# Зберігаємо ID ринків, які вже бачили
seen_markets = set()

# Нові ринки за останні 5 днів
NEW_DAYS = 5

# ---- Функції ----
def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("❌ Telegram error:", e)

def get_markets(limit=100, offset=0):
    url = f"https://gamma-api.polymarket.com/markets?tag_slug=crypto&limit={limit}&offset={offset}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        try:
            return r.json()
        except Exception as e:
            print("❌ Не вдалося прочитати JSON:", e)
            return []
    except Exception as e:
        print("❌ Помилка get_markets:", e)
        return []

def safe_parse_timestamp(created_at):
    try:
        dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        print("📅 Parsed timestamp:", created_at, "->", dt)
        return dt
    except ValueError:
        try:
            dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            print("📅 Parsed timestamp:", created_at, "->", dt)
            return dt
        except Exception as e:
            print("❌ Помилка конвертації timestamp:", created_at, e)
            return None

def check_markets():
    global seen_markets
    markets = get_markets()
    if not markets:
        print("⚠️ Немає даних")
        return

    new_found = 0
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=NEW_DAYS)

    for m in markets:
        market_id = m.get("id")
        title = m.get("question")
        created_at = m.get("createdAt")
        status = m.get("status")

        if not market_id or not title or not created_at or status != "open":
            continue

        created_dt = safe_parse_timestamp(created_at)
        if not created_dt or created_dt < threshold:
            continue

        if market_id not in seen_markets:
            liquidity = float(m.get("liquidity", 0) or 0)
            volume = float(m.get("volume", 0) or 0)
            link = f"https://polymarket.com{m.get('path','')}"

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

# ---- Старт бота ----
print("🚀 Bot started...")
print("⏳ Перевірка доступу до API...")

# Переконуємося, що API відповідає перед циклом
initial_markets = get_markets()
if not initial_markets:
    print("❌ API не відповідає, вихід...")
    exit(1)

# Ініціалізація лише нових ринків за 5 днів
now = datetime.now(timezone.utc)
threshold = now - timedelta(days=NEW_DAYS)
for m in initial_markets:
    market_id = m.get("id")
    created_at = m.get("createdAt")
    if market_id and created_at:
        created_dt = safe_parse_timestamp(created_at)
        if created_dt and created_dt >= threshold:
            seen_markets.add(market_id)

print(f"📦 Ініціалізовано: {len(seen_markets)} ринків (нових за {NEW_DAYS} днів)")
send_message(f"✅ Бот запущений і працює. Слідкує за ринками за останні {NEW_DAYS} днів")

# ---- Цикл перевірки кожну хвилину ----
while True:
    try:
        check_markets()
    except Exception as e:
        print("❌ Помилка в циклі:", e)
    time.sleep(60)