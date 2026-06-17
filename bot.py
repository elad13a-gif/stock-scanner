import logging
import requests as req
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from scanner import analyze, tech_score, position, get_maya_events, STOP_LOSS, TARGET

TOKEN = "8931673908:AAEAkLdaMDSobsY8VOO8gOsTPZzf7mBLy2E"
logging.basicConfig(level=logging.INFO)

MANUAL_STOCKS = {
    "SPCX": {
        "ticker":"SPCX","currency":"$","capital":5000,
        "price":201.80,"change":4.8,"rsi":72.0,
        "macd_bull":True,"trend_up":True,"vol_ratio":3.5,
        "pe_ratio":None,"eps":None,"market_cap":2_590_000_000_000,
        "new_stock":True,"special":False,
    }
}

def search_ticker(query):
    """
    מחפש סימול מניה לפי שם חופשי בעברית או אנגלית
    דרך Yahoo Finance ו-Finviz
    """
    headers = {"User-Agent": "Mozilla/5.0"}

    # ניסיון 1 — Yahoo Finance חיפוש חופשי
    try:
        url = (
            f"https://query2.finance.yahoo.com/v1/finance/search"
            f"?q={query}&lang=en&region=US&quotesCount=5&newsCount=0"
        )
        r      = req.get(url, headers=headers, timeout=8)
        data   = r.json()
        quotes = data.get("quotes", [])
        for q in quotes:
            qtype = q.get("quoteType","")
            if qtype in ("EQUITY","ETF"):
                return q.get("symbol"), q.get("longname") or q.get("shortname","")
    except:
        pass

    # ניסיון 2 — Yahoo Finance חיפוש בעברית דרך תרגום
    try:
        translate_url = (
            f"https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=he&tl=en&dt=t&q={req.utils.quote(query)}"
        )
        tr = req.get(translate_url, timeout=5).json()
        english = tr[0][0][0]
        url = (
            f"https://query2.finance.yahoo.com/v1/finance/search"
            f"?q={english}&lang=en&region=US&quotesCount=5&newsCount=0"
        )
        r      = req.get(url, headers=headers, timeout=8)
        data   = r.json()
        quotes = data.get("quotes", [])
        for q in quotes:
            if q.get("quoteType") in ("EQUITY","ETF"):
                return q.get("symbol"), q.get("longname") or q.get("shortname","")
    except:
        pass

    return None, None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    await update.message.reply_text(f"🔍 מחפש את '{text}'...")

    ticker       = None
    company_name = None
    data         = None

    # בדיקה ידנית קודם
    if text.upper() in MANUAL_STOCKS:
        ticker = text.upper()
        data   = MANUAL_STOCKS[ticker]

    # חיפוש חופשי באינטרנט
    if not data:
        ticker, company_name = search_ticker(text)

    # ניסיון ניתוח
    if ticker and not data:
        data = analyze(ticker)

    # ניסיון עם .TA
    if not data and ticker and not ticker.endswith(".TA"):
        data = analyze(ticker + ".TA")
        if data:
            ticker = ticker + ".TA"

    # ניסיון ישיר אם המשתמש כתב סימול
    if not data:
        direct = text.upper()
        data   = analyze(direct)
        if data:
            ticker = direct
        else:
            data = analyze(direct + ".TA")
            if data:
                ticker = direct + ".TA"

    if not data:
        await update.message.reply_text(
            f"❌ לא מצאתי את '{text}'\n\n"
            f"נסה לכתוב:\n"
            f"• סימול מדויק: NVDA, TEVA, AAPL\n"
            f"• שם באנגלית: nvidia, tesla, apple\n"
            f"• שם בעברית: נווידיה, טבע, אפל"
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
    if cap >= 1_000_000_000:
        cap_str = f"{cap/1_000_000_000:.1f}B"
    elif cap >= 1_000_000:
        cap_str = f"{cap/1_000_000:.0f}M"
    else:
        cap_str = "—"

    if score >= 80:   rec = "קנייה חזקה ✅✅"
    elif score >= 65: rec = "כניסה ✅"
    elif score >= 50: rec = "שמור על הגדר ⚠️"
    else:             rec = "אל תיכנס ❌"

    maya_line    = f"\n📢 המאיה: {', '.join(maya)}" if maya else ""
    special_line = "\n⭐ תנאים מיוחדים!" if data.get("special") else ""
    name         = company_name or ticker.replace(".TA","")

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
        f"{maya_line}{special_line}\n\n"
        f"💰 קנה: {cur}{amt} ({shares} מניות)\n"
        f"🎯 יעד: {cur}{target} (+5%)\n"
        f"🛑 סטופ: {cur}{stop} (-3%)\n"
        f"⏱ כניסה: 10-20 דק אחרי פתיחה\n\n"
        f"לא המלצת השקעה — לצורכי לימוד בלבד"
    )
    await update.message.reply_text(msg)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ הבוט פעיל — כתוב כל שם מניה בטלגרם!")
    app.run_polling()

if __name__ == "__main__":
    main()