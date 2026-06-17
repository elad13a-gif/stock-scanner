import sys
import schedule
import time
from scanner import run_scan
from notify  import send, format_message
import datetime

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
    # הרצה מ-Task Scheduler עם פרמטר
    if "--job" in sys.argv:
        job = sys.argv[sys.argv.index("--job") + 1]
        if job == "israel":
            scan_israel()
        elif job == "usa":
            scan_usa()
        sys.exit(0)

    # הרצה ידנית — מריץ לפי שעה
    hour = datetime.datetime.now().hour
    if hour < 12:
        scan_israel()
    else:
        scan_usa()