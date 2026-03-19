import requests
import time
from datetime import datetime, timedelta, timezone

TELEGRAM_TOKEN = "8667045124:AAGS4HceBcGJUAkGAZpqXAWUYmQAtJNzvEo"
CHAT_ID = "598513173"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"}

seen_markets = set()
NEW_DAYS = 5
LIMIT = 200

def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("❌ Telegram error:", e)

def parse_timestamp(created_at):
    try:
        return datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    except:
        try:
            return datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except:
            return None

def get_crypto_pre_market_all():
    """Забирає всі ринки в collection crypto/pre-market, включно з усіма підгілками"""
    all_markets = []
    offset = 0
    threshold = datetime.now(timezone.utc) - timedelta(days=NEW_DAYS)

    while True:
        params = {
            "collection": "crypto/pre-market",
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
            print("❌ API error:", e)
            break

        stop = False
        for m in markets:
            created_dt = parse_timestamp(m.get("createdAt"))
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
    markets = get_crypto_pre_market_all()
    if not markets:
        print(f"⚠️ Немає нових pre-market ринків за останні {NEW_DAYS} днів")
        return

    new_found = 0
    for m in markets:
        market_id = m.get("id")
        title = m.get("question","")
        slug = m.get("slug","")
        link = f"https://polymarket.com/event/{slug}" if slug else f"https://polymarket.com/event/{market_id}"

        if not market_id or not title:
            continue

        if market_id not in seen_markets:
            liquidity = float(m.get("liquidity",0) or 0)
            volume = float(m.get("volume",0) or 0)

            message = (
                f"🆕 <b>{title}</b>\n\n"
                f"💰 Ліквідність: ${liquidity:,.0f}\n"
                f"📊 Обсяг: ${volume:,.0f}\n"
                f"🔗 <a href='{link}'>Відкрити ринок</a>"
            )

            send_message(message)
            print("🆕 pre-market:", title)
            new_found += 1

        seen_markets.add(market_id)

    print(f"✅ Нових pre-market ринків: {new_found}")
    print("------")

# ---- Старт бота ----
print("🚀 Bot started...")
send_message(f"✅ Бот запущений — слідкує за всіма pre-market ринками ({NEW_DAYS} днів)")

while True:
    try:
        check_markets()
    except Exception as e:
        print("❌ Bot loop error:", e)
    time.sleep(60)