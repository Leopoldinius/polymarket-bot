import requests
import time
from datetime import datetime, timedelta, timezone

# 🔑 Встав свій токен та чат
TELEGRAM_TOKEN = "8667045124:AAGS4HceBcGJUAkGAZpqXAWUYmQAtJNzvEo"
CHAT_ID = "598513173"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"}

seen_markets = set()
NEW_DAYS = 5
LIMIT = 100  # кількість ринків за запит

def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("❌ Telegram error:", e)

def safe_parse_timestamp(created_at):
    try:
        dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        try:
            dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            return dt
        except Exception as e:
            print("❌ Помилка конвертації timestamp:", created_at, e)
            return None

def get_all_recent_markets():
    all_markets = []
    offset = 0
    threshold = datetime.now(timezone.utc) - timedelta(days=NEW_DAYS)

    while True:
        params = {
            "active": "true",
            "closed": "false",
            "limit": LIMIT,
            "offset": offset,
            "order": "createdAt",
            "ascending": "false"
        }
        try:
            r = requests.get("https://gamma-api.polymarket.com/markets", params=params, headers=HEADERS, timeout=15)
            r.raise_for_status()
            markets = r.json()
            if not markets:
                break
        except Exception as e:
            print("❌ Помилка get_markets:", e)
            break

        stop = False
        for m in markets:
            created_dt = safe_parse_timestamp(m.get("createdAt"))
            if not created_dt:
                continue
            if created_dt < threshold:
                stop = True
                break
            all_markets.append(m)

        if stop or len(markets) < LIMIT:
            break

        offset += LIMIT

    return all_markets

def check_markets():
    global seen_markets
    markets = get_all_recent_markets()
    if not markets:
        print("⚠️ Немає нових ринків за останні 5 днів")
        return

    new_found = 0
    for m in markets:
        market_id = m.get("id")
        title = m.get("question")
        liquidity = float(m.get("liquidity", 0) or 0)
        volume = float(m.get("volume", 0) or 0)
        link = f"https://polymarket.com{m.get('path','')}"

        if not market_id or not title:
            continue

        if market_id not in seen_markets:
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
send_message(f"✅ Бот запущений і стежить за ринками за останні {NEW_DAYS} днів")

while True:
    try:
        check_markets()
    except Exception as e:
        print("❌ Помилка в циклі:", e)
    time.sleep(60)