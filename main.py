import sys
import schedule
import time
import datetime
from scanner import run_scan
from notify  import send, format_message

def scan_israel():
    print("סריקת בוקר - ת\"א 125...")
    recs = run_scan("IL")
    if recs:
        msg = "🇮🇱 08:30 — המלצות לפני פתיחת ת\"א 125\n\n" + format_message(recs)
    else:
        msg = "🇮🇱 08:30 — אין המלצות כניסה לת\"א היום"
    send(msg)

def scan_usa():
    print("סריקה - לפני פתיחת ארה\"ב...")
    recs = run_scan("US")
    if recs:
        msg = "🇺🇸 15:45 — המלצות לפני פתיחת וול סטריט\n\n" + format_message(recs)
    else:
        msg = "🇺🇸 15:45 — אין המלצות כניסה לארה\"ב היום"
    send(msg)

if __name__ == "__main__":
    print("✅ סורק מניות פעיל!")

    # תזמון יומי
    schedule.every().day.at("08:30").do(scan_israel)
    schedule.every().day.at("15:45").do(scan_usa)

    print("   08:30 — ת\"א 125")
    print("   15:45 — נאסד\"ק + S&P")

    # לולאה אינסופית — שומרת את התוכנה פעילה
    while True:
        schedule.run_pending()
        time.sleep(60)