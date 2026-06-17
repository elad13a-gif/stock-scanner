import yfinance as yf
import pandas as pd
import ta
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

STOP_LOSS = 0.03
TARGET    = 0.05

# ─── שאיבת מניות חמות מהרשת ───────────────────────────
def fetch_hot_tickers_us():
    """
    שואב מניות חמות מ-Finviz ו-Yahoo Finance
    מחזיר רשימה של סימולים
    """
    tickers = set()
    headers = {"User-Agent": "Mozilla/5.0"}

    # מקור 1 — Finviz: מניות עם עלייה חזקה ונפח גבוה היום
    try:
        url  = "https://finviz.com/screener.ashx?v=111&s=ta_topgainers&f=sh_price_o5,sh_vol_o500"
        r    = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", class_="screener-link-primary"):
            tickers.add(a.text.strip())
        print(f"  Finviz gainers: {len(tickers)} מניות")
    except Exception as e:
        print(f"  Finviz שגיאה: {e}")

    # מקור 2 — Finviz: מניות עם נפח חריג
    try:
        url  = "https://finviz.com/screener.ashx?v=111&s=ta_unusualvolume&f=sh_price_o5"
        r    = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", class_="screener-link-primary"):
            tickers.add(a.text.strip())
        print(f"  Finviz volume: סה\"כ {len(tickers)} מניות")
    except Exception as e:
        print(f"  Finviz volume שגיאה: {e}")

    # מקור 3 — Yahoo Finance: מניות מובילות
    try:
        urls = [
            "https://finance.yahoo.com/gainers",
            "https://finance.yahoo.com/most-active",
        ]
        for url in urls:
            r    = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", attrs={"data-testid": "table-cell-ticker"}):
                tickers.add(a.text.strip())
        print(f"  Yahoo Finance: סה\"כ {len(tickers)} מניות")
    except Exception as e:
        print(f"  Yahoo שגיאה: {e}")

    # מקור 4 — Finviz: מניות בפריצת שיא
    try:
        url  = "https://finviz.com/screener.ashx?v=111&s=ta_newhigh&f=sh_price_o5"
        r    = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", class_="screener-link-primary"):
            tickers.add(a.text.strip())
        print(f"  Finviz new highs: סה\"כ {len(tickers)} מניות")
    except Exception as e:
        print(f"  Finviz highs שגיאה: {e}")

    result = [t for t in tickers if t and len(t) <= 5 and t.isalpha()]
    print(f"\n  ✅ סה\"כ {len(result)} מניות ארה\"ב לסריקה")
    return result


def fetch_hot_tickers_il():
    """
    שואב מניות חמות מהמאיה ומבורסת ת"א
    """
    tickers = set()
    headers = {"User-Agent": "Mozilla/5.0"}

    # מקור 1 — המאיה: מניות עם אירועי חדשות
    try:
        url  = "https://maya.tase.co.il/reports/company"
        r    = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup.find_all(["span","div","td"], class_=lambda c: c and "symbol" in c.lower()):
            t = tag.text.strip()
            if t:
                tickers.add(t + ".TA")
        print(f"  המאיה: {len(tickers)} מניות")
    except Exception as e:
        print(f"  המאיה שגיאה: {e}")

    # מקור 2 — Yahoo Finance ת"א: מניות מובילות
    try:
        url  = "https://finance.yahoo.com/quote/%5ETA125.TA/components"
        r    = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", attrs={"data-testid": "table-cell-ticker"}):
            t = a.text.strip()
            if not t.endswith(".TA"):
                t += ".TA"
            tickers.add(t)
        print(f"  Yahoo ת\"א: סה\"כ {len(tickers)} מניות")
    except Exception as e:
        print(f"  Yahoo ת\"א שגיאה: {e}")

    # ─── רזרבה: רשימת ליבה של ת"א 125 ────────────────
    core_il = [
        "TEVA.TA","NICE.TA","CHKP.TA","MNDY.TA","WIX.TA","GLBE.TA",
        "ICL.TA","ESLT.TA","AMOT.TA","MGDL.TA","HARL.TA","PHOE.TA",
        "DSCT.TA","LUMI.TA","POLI.TA","MZRH.TA","FIBI.TA","ITRN.TA",
        "ENLT.TA","SPEN.TA","CAMT.TA","CRNT.TA","NVMI.TA","RDRD.TA",
        "TSEM.TA","SMDR.TA","SKBN.TA","PRGO.TA","GILT.TA","STRS.TA",
    ]
    for t in core_il:
        tickers.add(t)

    result = list(tickers)
    print(f"\n  ✅ סה\"כ {len(result)} מניות ת\"א לסריקה")
    return result


# ─── בדיקת אירועי המאיה ───────────────────────────────
def get_maya_events(ticker):
    events = []
    try:
        clean   = ticker.replace(".TA", "")
        url     = f"https://maya.tase.co.il/company/{clean}/reports"
        headers = {"User-Agent": "Mozilla/5.0"}
        r       = requests.get(url, headers=headers, timeout=8)
        text    = r.text.lower()
        if "גיוס הון" in text or "capital raise" in text:
            events.append("גיוס הון")
        if "רכישה" in text or "acquisition" in text:
            events.append("רכישה")
        if "חוזה חדש" in text or "new contract" in text:
            events.append("חוזה חדש")
        if "מכרז" in text or "tender" in text:
            events.append("זכייה במכרז")
    except:
        pass
    return events


# ─── בדיקת תנאים מיוחדים ──────────────────────────────
def check_special_conditions(data, hist_1y):
    conditions = 0
    if data["change"] >= 4.0:
        conditions += 1
    try:
        high_52w = float(hist_1y["High"].max())
        if data["price"] >= high_52w * 0.98:
            conditions += 1
    except:
        pass
    try:
        if len(hist_1y) >= 63:
            price_3m = float(hist_1y["Close"].squeeze().iloc[-63])
            if data["price"] > price_3m:
                conditions += 1
    except:
        pass
    if data.get("market_cap", 0) >= 150_000_000:
        conditions += 1
    return conditions >= 3


# ─── ניתוח טכני + פונדמנטלי ───────────────────────────
def analyze(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1d",
                         progress=False, auto_adjust=True)
        if df is None or len(df) < 3:
            df = yf.download(ticker, period="5d", interval="1d",
                             progress=False, auto_adjust=True)
            if df is not None and len(df) >= 2:
                price  = float(df["Close"].squeeze().iloc[-1])
                prev   = float(df["Close"].squeeze().iloc[-2])
                change = (price - prev) / prev * 100
                is_il  = ".TA" in ticker
                return {
                    "ticker":     ticker,
                    "currency":   "₪" if is_il else "$",
                    "capital":    18000 if is_il else 5000,
                    "price":      round(price, 2),
                    "change":     round(change, 2),
                    "rsi":        50.0,
                    "macd_bull":  change > 0,
                    "trend_up":   change > 0,
                    "vol_ratio":  1.5,
                    "pe_ratio":   None,
                    "eps":        None,
                    "market_cap": 0,
                    "new_stock":  True,
                }
            return None

        if len(df) < 20:
            return None

        close     = df["Close"].squeeze()
        volume    = df["Volume"].squeeze()
        price     = float(close.iloc[-1])
        prev      = float(close.iloc[-2])
        change    = (price - prev) / prev * 100
        avg_vol   = float(volume.rolling(20).mean().iloc[-2])
        vol_ratio = float(volume.iloc[-1]) / avg_vol if avg_vol > 0 else 1.0

        rsi       = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]
        macd      = ta.trend.MACD(close)
        macd_bull = macd.macd().iloc[-1] > macd.macd_signal().iloc[-1]
        ema20     = ta.trend.EMAIndicator(close, window=20).ema_indicator().iloc[-1]
        ema50     = ta.trend.EMAIndicator(close, window=50).ema_indicator().iloc[-1]

        try:
            info     = yf.Ticker(ticker).info
            pe_ratio = info.get("trailingPE") or info.get("forwardPE")
            eps      = info.get("trailingEps")
            mkt_cap  = info.get("marketCap", 0)
        except:
            pe_ratio = None
            eps      = None
            mkt_cap  = 0

        is_il = ".TA" in ticker
        return {
            "ticker":     ticker,
            "currency":   "₪" if is_il else "$",
            "capital":    18000 if is_il else 5000,
            "price":      round(price, 2),
            "change":     round(change, 2),
            "rsi":        round(float(rsi), 1),
            "macd_bull":  bool(macd_bull),
            "trend_up":   bool(ema20 > ema50),
            "vol_ratio":  round(vol_ratio, 2),
            "pe_ratio":   round(pe_ratio, 1) if pe_ratio else None,
            "eps":        round(eps, 2) if eps else None,
            "market_cap": mkt_cap,
            "new_stock":  False,
        }
    except Exception as e:
        return None


# ─── ציון ─────────────────────────────────────────────
def tech_score(data):
    if data.get("new_stock"):
        return 55
    s = 0
    rsi = data["rsi"]
    if 50 <= rsi <= 62:   s += 30
    elif 45 <= rsi < 50:  s += 15
    elif 62 < rsi <= 68:  s += 15
    if data["macd_bull"]: s += 20
    if data["trend_up"]:  s += 20
    vr = data["vol_ratio"]
    if vr >= 2.0:         s += 15
    elif vr >= 1.5:       s += 10
    elif vr >= 1.2:       s += 5
    pe = data.get("pe_ratio")
    if pe and pe > 25:    s += 10
    eps = data.get("eps")
    if eps and eps > 0:   s += 5
    return min(s, 100)


# ─── גודל פוזיציה ─────────────────────────────────────
def position(score_val, capital):
    if score_val >= 85:   pct = 0.17
    elif score_val >= 75: pct = 0.14
    elif score_val >= 65: pct = 0.11
    else:                 pct = 0.08
    return round(capital * pct)


# ─── סריקה מקבילית מהירה ──────────────────────────────
def scan_one(ticker):
    data = analyze(ticker)
    if not data:
        return None
    ts = tech_score(data)
    maya_events = []
    if ".TA" in ticker:
        maya_events = get_maya_events(ticker)
        if maya_events:
            ts += 10
    try:
        hist_1y = yf.download(ticker, period="1y", interval="1d",
                              progress=False, auto_adjust=True)
        if check_special_conditions(data, hist_1y):
            ts += 15
            data["special"] = True
        else:
            data["special"] = False
    except:
        data["special"] = False

    s   = min(ts, 100)
    amt = position(s, data["capital"])
    return {
        **data,
        "score":       s,
        "invest":      amt,
        "shares":      max(1, int(amt // data["price"])),
        "stop":        round(data["price"] * (1 - STOP_LOSS), 2),
        "target":      round(data["price"] * (1 + TARGET), 2),
        "maya_events": maya_events,
        "rec":         "כניסה ✅" if s >= 60 else "המתן ⏳",
    }


# ─── סריקה ראשית ──────────────────────────────────────
def run_scan(market="IL"):
    if market == "IL":
        print("\n🇮🇱 שואב מניות חמות מת\"א...")
        tickers = fetch_hot_tickers_il()
    elif market == "US":
        print("\n🇺🇸 שואב מניות חמות מארה\"ב...")
        tickers = fetch_hot_tickers_us()
    else:
        print("\n🌍 שואב מניות חמות מכל השווקים...")
        tickers = fetch_hot_tickers_us() + fetch_hot_tickers_il()

    print(f"\n🔍 מנתח {len(tickers)} מניות במקביל...")

    with ThreadPoolExecutor(max_workers=10) as ex:
        raw = list(ex.map(scan_one, tickers))

    results = [r for r in raw if r]
    results.sort(key=lambda x: x["score"], reverse=True)
    top = results[:5]

    print(f"\n✅ 5 המניות המובילות:\n")
    for i, r in enumerate(top, 1):
        cur = r["currency"]
        print(f"  {i}. {r['ticker']:12s} ציון={r['score']} "
              f"קנה={cur}{r['invest']} "
              f"יעד={cur}{r['target']} "
              f"סטופ={cur}{r['stop']}")
    return top


if __name__ == "__main__":
    run_scan("US")