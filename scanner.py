import yfinance as yf
import pandas as pd
import ta
import requests
import time
from bs4 import BeautifulSoup

STOP_LOSS = 0.03
TARGET    = 0.05

# ══ רשימת גיבוי — ת"א 125 ══
BACKUP_IL = [
    "TEVA.TA","NICE.TA","CHKP.TA","MNDY.TA","WIX.TA","GLBE.TA",
    "ICL.TA","ESLT.TA","AMOT.TA","MGDL.TA","HARL.TA","PHOE.TA",
    "DSCT.TA","LUMI.TA","POLI.TA","MZRH.TA","FIBI.TA","ITRN.TA",
    "ENLT.TA","SPEN.TA","CAMT.TA","CRNT.TA","NVMI.TA","RDRD.TA",
    "TSEM.TA","SMDR.TA","SKBN.TA","PRGO.TA","GILT.TA","STRS.TA",
]

# ══ רשימת גיבוי — נאסד"ק + S&P ══
BACKUP_US = [
    "NVDA","AAPL","MSFT","AMZN","GOOGL","META","TSLA","AMD","AVGO","MU",
    "PLTR","APP","CRWD","PANW","ARM","MRVL","ASML","NFLX","COST","SBUX",
    "JPM","BAC","GS","V","MA","BRK-B","JNJ","LLY","UNH","ABBV",
    "XOM","CVX","HD","WMT","MCD","KO","PG","AMGN","GILD","VRTX",
    "NEE","AMT","EQIX","PLD","COIN","UBER","SHOP","SNOW","DDOG","NET",
]


# ─── שאיבת מניות חמות מהרשת ───────────────────────────
def fetch_hot_us():
    tickers = set()
    headers = {"User-Agent": "Mozilla/5.0"}

    # Yahoo Finance — מניות מובילות
    urls = [
        "https://finance.yahoo.com/gainers",
        "https://finance.yahoo.com/most-active",
        "https://finance.yahoo.com/trending-tickers",
    ]
    for url in urls:
        try:
            r    = requests.get(url, headers=headers, timeout=8)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", attrs={"data-testid": "table-cell-ticker"}):
                t = a.text.strip()
                if t and len(t) <= 5:
                    tickers.add(t)
            for fin_stream in soup.find_all("fin-streamer", attrs={"data-symbol": True}):
                t = fin_stream.get("data-symbol","").strip()
                if t and len(t) <= 5 and t.isalpha():
                    tickers.add(t)
        except:
            pass

    result = list(tickers)
    if len(result) < 20:
        print("  משתמש ברשימת גיבוי")
        result = BACKUP_US
    else:
        # מוסיף מניות גיבוי חשובות
        result = list(set(result) | set(BACKUP_US[:20]))

    print(f"  {len(result)} מניות ארה\"ב לסריקה")
    return result


def fetch_hot_il():
    tickers = set()
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        url  = "https://maya.tase.co.il/reports/company"
        r    = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup.find_all(["span","td"], string=True):
            t = tag.text.strip()
            if t and 2 <= len(t) <= 6 and t.isupper():
                tickers.add(t + ".TA")
    except:
        pass

    result = list(tickers) if len(tickers) > 10 else []
    result = list(set(result) | set(BACKUP_IL))
    print(f"  {len(result)} מניות ת\"א לסריקה")
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
    except:
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


# ─── סריקה ────────────────────────────────────────────
def run_scan(market="IL"):
    if market == "IL":
        print("\nשואב מניות חמות מת\"א...")
        tickers = fetch_hot_il()
    elif market == "US":
        print("\nשואב מניות חמות מארה\"ב...")
        tickers = fetch_hot_us()
    else:
        tickers = fetch_hot_il() + fetch_hot_us()

    print(f"מנתח {len(tickers)} מניות...")

    results = []
    for ticker in tickers:
        data = analyze(ticker)
        if not data:
            continue

        ts = tech_score(data)

        maya_events = []
        if ".TA" in ticker:
            maya_events = get_maya_events(ticker)
            if maya_events:
                ts += 10

        s   = min(ts, 100)
        amt = position(s, data["capital"])

        results.append({
            **data,
            "score":       s,
            "invest":      amt,
            "shares":      max(1, int(amt // data["price"])),
            "stop":        round(data["price"] * (1 - STOP_LOSS), 2),
            "target":      round(data["price"] * (1 + TARGET), 2),
            "maya_events": maya_events,
            "special":     False,
            "rec":         "כניסה" if s >= 60 else "המתן",
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    top = results[:5]

    print(f"\n5 המניות המובילות:")
    for i, r in enumerate(top, 1):
        cur = r["currency"]
        print(f"  {i}. {r['ticker']:12s} ציון={r['score']} "
              f"קנה={cur}{r['invest']} "
              f"יעד={cur}{r['target']} "
              f"סטופ={cur}{r['stop']}")
    return top


if __name__ == "__main__":
    run_scan("US")