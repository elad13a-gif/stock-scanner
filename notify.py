import requests

TOKEN   = "8931673908:AAEAkLdaMDSobsY8VOO8gOsTPZzf7mBLy2E"
CHAT_ID = "840664684"

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
    lines = ["5 המניות המומלצות:\n"]
    for i, r in enumerate(recs, 1):
        cur = r.get("currency", "$")
        lines += [
            f"{i}. {r['ticker'].replace('.TA','')} | ציון: {r['score']}",
            f"   קנה: {cur}{r['invest']} ({r['shares']} מניות)",
            f"   יעד: {cur}{r['target']} (+5%)",
            f"   סטופ: {cur}{r['stop']} (-3%)",
            f"   כניסה: 10-20 דק אחרי פתיחה\n",
        ]
    lines.append("לא המלצת השקעה - לצורכי לימוד בלבד")
    return "\n".join(lines)

if __name__ == "__main__":
    send("בוט מניות פעיל ומחובר!")