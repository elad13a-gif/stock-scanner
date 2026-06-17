import sys
import schedule
import time
import datetime
import asyncio
import threading
from scanner import run_scan
from notify  import send, format_message
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from scanner import analyze, tech_score, position, get_maya_events, STOP_LOSS, TARGET
import requests as req

TOKEN   = "8931673908:AAEAkLdaMDSobsY8VOO8gOsTPZzf7mBLy2E"
CHAT_ID = "840664684"

# ─── פונקציות סריקה ───────────────────────────────────
def scan_israel():
    print("סריקת בוקר - ת\"א 125...")
    recs = run_scan("IL")
    msg  = "🇮🇱 08:30 — המלצות לפני פתיחת ת\"א 125\n\n" + format_message(recs) if recs else "🇮🇱 אין המלצות היום"
    send(msg)

def scan_usa():
    print("סריקה - לפני פתיחת ארה\"ב...")
    recs = run_scan("US")
    msg  = "🇺🇸 15:45 — המלצות לפני וול סטריט\n\n" + format_message(recs) if recs else "🇺🇸 אין המלצות היום"
    send(msg)

def run_scheduler():
    schedule.every().day.at("08:30").do(scan_israel)
    schedule.every().day.at("15:45").do(scan_usa)
    print("✅ סורק פעיל! 08:30 ת\"א | 15:45 ארה\"ב")
    while True:
        schedule.run_pending()
        time.sleep(60)

# ─── בוט טלגרם ────────────────────────────────────────
def search_ticker(query):
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&lang=en&region=US&quotesCount=5&newsCount=0"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = req.get(url, headers=headers, timeout=8)
        quotes = r.json().get("quotes", [])
        for q in quotes:
            if q.get("quoteType") in ("EQUITY","ETF"):
                return q.get("symbol"), q.get("longname") or q.get("shortname","")
    except:
        pass
    return None, None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    await update.message.reply_text(f"🔍 מחפש את '{text}'...")

    ticker, company_name = search_ticker(text)
    if not ticker:
        ticker = text.upper()

    data = analyze(ticker)
    if not data:
        data = analyze(ticker + ".TA")
        if data:
            ticker = ticker + ".TA"

    if not data:
        await update.message.reply_text(
            f"❌ לא מצאתי את '{text}'\n\n"
            f"נסה: NVDA, TEVA, AAPL\n"
            f"או: nvidia, tesla, apple"
        )
        return

    ts     = tech_score(data)
    maya   = get_maya_events(ticker) if ".TA" in ticker else []
    if maya: ts += 10
    score  = min(ts, 100)
    cur    = data["currency"]
    amt    = position(score, data["capital"])
    shares = max(1, int(amt // data["price"]))
    stop   = round(data["price"] * (1 - STOP_LOSS), 2)
    target = round(data["price"] * (1 + TARGET), 2)
    pe     = str(data["pe_ratio"]) if data.get("pe_ratio") else "—"
    eps    = str(data["eps"])      if data.get("eps")      else "—"
    cap    = data.get("market_cap", 0)
    cap_str = f"{cap/1_000_000_000:.1f}B" if cap >= 1_000_000_000 else f"{cap/1_000_000:.0f}M" if cap >= 1_000_000 else "—"

    if score >= 80:   rec = "קנייה חזקה ✅✅"
    elif score >= 65: rec = "כניסה ✅"
    elif score >= 50: rec = "שמור על הגדר ⚠️"
    else:             rec = "אל תיכנס ❌"

    maya_line = f"\n📢 המאיה: {', '.join(maya)}" if maya else ""
    name      = company_name or ticker.replace(".TA","")

    msg = (
        f"📊 {name} ({ticker.replace('.TA','')})\n\n"
        f"המלצה: {rec}\n"
        f"ציון: {score}/100\n\n"
        f"מחיר: {cur}{data['price']} | שינוי: {data['change']:+.1f}%\n"
        f"RSI: {data['rsi']} | נפח: x{data['vol_ratio']}\n"
        f"מכפיל רווח: {pe} | EPS: {eps}\n"
        f"שווי שוק: {cap_str}\n"
        f"מומנטום: {'חיובי ↑' if data['macd_bull'] else 'שלילי ↓'}\n"
        f"טרנד: {'עולה ↑' if data['trend_up'] else 'יורד ↓'}\n"
        f"{maya_line}\n\n"
        f"💰 קנה: {cur}{amt} ({shares} מניות)\n"
        f"🎯 יעד: {cur}{target} (+5%)\n"
        f"🛑 סטופ: {cur}{stop} (-3%)\n"
        f"⏱ כניסה: 10-20 דק אחרי פתיחה\n\n"
        f"לא המלצת השקעה — לצורכי לימוד בלבד"
    )
    await update.message.reply_text(msg)

def run_bot():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ בוט טלגרם פעיל!")
    app.run_polling()

# ─── הרצה ראשית ───────────────────────────────────────
if __name__ == "__main__":
    # הרץ את הסורק בthread נפרד
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # הרץ את הבוט בthread הראשי
    run_bot()