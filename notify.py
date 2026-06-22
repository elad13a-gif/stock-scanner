TOKEN   = "8931673908:AAEAkLdaMDSobsY8VOO8gOsTPZzf7mBLy2E"
CHAT_ID = "840664684"

import requests

def send(message):
    url  = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=data, timeout=10)
        r.raise_for_status()
        print("נשלח לטלגרם")
    except Exception as e:
        print(f"שגיאה: {e}")

def format_message(recs):
    if not recs:
        return "אין המלצות כניסה היום."

    lines = [f"🏆 {len(recs)} המלצות מובילות:\n"]

    for i, r in enumerate(recs, 1):
        cur = r.get("currency", "$")

        # נתונים בסיסיים
        pe      = f"{r['pe_ratio']}" if r.get("pe_ratio") else "—"
        eps     = f"{r['eps']}"      if r.get("eps")      else "—"
        cap     = r.get("market_cap", 0)
        cap_str = f"{cap/1_000_000_000:.1f}B" if cap >= 1_000_000_000 else \
                  f"{cap/1_000_000:.0f}M"      if cap >= 1_000_000      else "—"

        # תנאים מיוחדים
        special_line = "\n⭐ עומד ב-3+ תנאים מיוחדים!" if r.get("special") else ""

        # אירועי המאיה
        maya_events = r.get("maya_events", [])
        maya_line   = f"\n📢 המאיה: {', '.join(maya_events)}" if maya_events else ""

        # מכפיל רווח
        pe_flag = " ✅" if r.get("pe_ratio") and r["pe_ratio"] > 25 else ""

        lines += [
            f"{i}. <b>{r['ticker'].replace('.TA','')}</b> | ציון: {r['score']}",
            f"   💰 קנה: {cur}{r['invest']} ({r['shares']} מניות)",
            f"   🎯 יעד: {cur}{r['target']} (+5%)",
            f"   🛑 סטופ: {cur}{r['stop']} (-3%)",
            f"   ─────────────────",
            f"   📊 RSI: {r['rsi']} | נפח: x{r['vol_ratio']}",
            f"   📈 שינוי יומי: {r['change']:+.1f}%",
            f"   💵 מכפיל רווח: {pe}{pe_flag} | EPS: {eps}",
            f"   🏢 שווי שוק: {cap_str}",
            f"   📉 מומנטום: {'חיובי ↑' if r['macd_bull'] else 'שלילי ↓'} | טרנד: {'עולה ↑' if r['trend_up'] else 'יורד ↓'}",
            f"{maya_line}{special_line}",
            f"   ⏱ כניסה: 10-20 דק אחרי פתיחה\n",
        ]

    lines.append("⚠️ לא המלצת השקעה — לצורכי לימוד בלבד")
    return "\n".join(lines)