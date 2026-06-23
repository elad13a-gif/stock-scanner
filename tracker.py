"""
tracker.py — מעקב אחרי מניות מומלצות
בודק כל 5 דקות ושולח התראות
"""
import yfinance as yf
import time
from notify import send
from datetime import datetime
import pytz

tz = pytz.timezone("Asia/Jerusalem")

TRACKED = {}

def add_recommendation(recs: list):
    TRACKED.clear()
    for r in recs:
        TRACKED[r["ticker"]] = {
            "price_at_rec": r["price"],
            "stop":         r["stop"],
            "target":       r["target"],
            "currency":     r["currency"],
            "alerted":      False,
            "rec_data":     r,  # שמירת כל הנתונים
        }
    print(f"📍 עוקב אחרי {len(TRACKED)} מניות")
def get_current_price(ticker: str):
    try:
        t    = yf.Ticker(ticker)
        data = t.fast_info
        return float(data.last_price)
    except:
        return None

def check_alerts():
    if not TRACKED:
        return
    now = datetime.now(tz)
    if now.weekday() >= 5:
        return
    if not (9 <= now.hour <= 17):
        return

    for ticker, info in TRACKED.items():
        if info["alerted"]:
            continue
        price = get_current_price(ticker)
        if not price:
            continue
        entry  = info["price_at_rec"]
        change = (price - entry) / entry * 100
        cur    = info["currency"]
        name   = ticker.replace(".TA","")

        if price >= info["target"]:
            send(
                f"🎯 יעד הושג!\n\n"
                f"<b>{name}</b> הגיעה ליעד +5%\n"
                f"מחיר כניסה: {cur}{entry}\n"
                f"מחיר עכשיו: {cur}{price:.2f}\n"
                f"רווח: +{change:.1f}%\n\n"
                f"💡 שקול למכור עכשיו!"
            )
            info["alerted"] = True

        elif price <= info["stop"]:
            send(
                f"🛑 סטופ לוס!\n\n"
                f"<b>{name}</b> ירדה מתחת לסטופ\n"
                f"מחיר כניסה: {cur}{entry}\n"
                f"מחיר עכשיו: {cur}{price:.2f}\n"
                f"הפסד: {change:.1f}%\n\n"
                f"⚠️ שקול לצאת עכשיו!"
            )
            info["alerted"] = True

        elif change <= -2.0:
            send(
                f"⚠️ אזהרה — ירידה של 2%\n\n"
                f"<b>{name}</b> ירדה {change:.1f}%\n"
                f"מחיר כניסה: {cur}{entry}\n"
                f"מחיר עכשיו: {cur}{price:.2f}\n"
                f"סטופ לוס: {cur}{info['stop']}\n\n"
                f"עדיין מעל הסטופ — עקוב מקרוב"
            )

def send_opening_update():
    if not TRACKED:
        return
    lines = ["📊 עדכון פתיחת מסחר — 10 דקות\n"]
    for ticker, info in TRACKED.items():
        price = get_current_price(ticker)
        if not price:
            continue
        entry  = info["price_at_rec"]
        change = (price - entry) / entry * 100
        cur    = info["currency"]
        name   = ticker.replace(".TA","")
        emoji  = "🟢" if change > 0 else "🔴"
        arrow  = "↑" if change > 0 else "↓"

        rec = info.get("rec_data", {})
        pe      = str(rec.get("pe_ratio","—")) if rec.get("pe_ratio") else "—"
        eps     = str(rec.get("eps","—"))      if rec.get("eps")      else "—"
        cap     = rec.get("market_cap", 0)
        cap_str = f"{cap/1_000_000_000:.1f}B" if cap >= 1_000_000_000 else \
                  f"{cap/1_000_000:.0f}M"      if cap >= 1_000_000      else "—"

        lines.append(
            f"{emoji} <b>{name}</b> {arrow} {change:+.1f}%\n"
            f"   כניסה: {cur}{entry} → עכשיו: {cur}{price:.2f}\n"
            f"   RSI: {rec.get('rsi','—')} | נפח: x{rec.get('vol_ratio','—')}\n"
            f"   מכפיל רווח: {pe} | EPS: {eps} | שווי שוק: {cap_str}\n"
            f"   יעד: {cur}{info['target']} | סטופ: {cur}{info['stop']}"
        )
    send("\n".join(lines))
def run_tracker():
    print("📍 מעקב מניות פעיל")
    checked_opening_il  = False
    checked_opening_us  = False

    while True:
        now = datetime.now(tz)

        # עדכון פתיחה ת"א ב-10:10
        if now.hour == 10 and now.minute == 10 and not checked_opening_il:
            send_opening_update()
            checked_opening_il = True

        # עדכון פתיחה ארה"ב ב-16:10
        if now.hour == 16 and now.minute == 10 and not checked_opening_us:
            send_opening_update()
            checked_opening_us = True

        # איפוס בסוף יום
        if now.hour == 18 and now.minute == 0:
            checked_opening_il = False
            checked_opening_us = False
            TRACKED.clear()

        # בדיקת התראות כל 5 דקות
        check_alerts()
        time.sleep(300)