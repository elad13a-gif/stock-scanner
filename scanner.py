import yfinance as yf
import pandas as pd
import ta
import requests
import time
from bs4 import BeautifulSoup

STOP_LOSS = 0.03
TARGET    = 0.05

# ══ נאסד"ק 100 — רשימה רשמית יוני 2026 ══
# כולל שינויי רבעון: ALAB, CRWV, NBIS, RKLB, TER נכנסו
# CHTR, CTSH, INSM, VRSK, ZS יצאו
WATCHLIST_NASDAQ = [
    "NVDA","AAPL","MSFT","AMZN","GOOGL","GOOG","AVGO","TSLA","META","MU",
    "WMT","AMD","ASML","INTC","LRCX","AMAT","CSCO","ARM","COST","KLAC",
    "SNDK","NFLX","TXN","PLTR","MRVL","WDC","STX","LIN","QCOM","PANW",
    "ADI","TMUS","PEP","AMGN","CRWD","APP","GILD","HON","ISRG","SHOP",
    "BKNG","VRTX","SBUX","PDD","CDNS","FTNT","MAR","CEG","MNST","SNPS",
    "CSX","ADP","ABNB","NXPI","MELI","CMCSA","DDOG","ADBE","MDLZ","ROST",
    "MPWR","ALAB","DASH","NBIS","TER","ORLY","AEP","INTU","LITE","CTAS",
    "REGN","PCAR","RKLB","CRWV","BKR","MCHP","FAST","FANG","EA","FER",
    "XEL","EXC","ODFL","TTWO","IDXX","CCEP","KDP","ADSK","MSTR","ALNY",
    "PYPL","PAYX","TRI","AXON","ROP","WDAY","GEHC","CPRT","DXCM","KHC",
    "WBD",
]

# ══ S&P 500 — רשימה רשמית מלאה יוני 2026 (503 מניות) ══
WATCHLIST_SP500 = [
    "MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AES","AFL","A",
    "APD","ABNB","AKAM","ALB","ARE","ALGN","ALLE","LNT","ALL","GOOGL",
    "GOOG","MO","AMZN","AMCR","AEE","AEP","AXP","AIG","AMT","AWK",
    "AMP","AME","AMGN","APH","ADI","AON","APA","APO","AAPL","AMAT",
    "APP","APTV","ACGL","ADM","ARES","ANET","AJG","AIZ","T","ATO",
    "ADSK","ADP","AZO","AVB","AVY","AXON","BKR","BALL","BAC","BAX",
    "BDX","BRK-B","BBY","TECH","BIIB","BLK","BX","XYZ","BNY","BA",
    "BKNG","BSX","BMY","AVGO","BR","BRO","BF-B","BLDR","BG","BXP",
    "CHRW","CDNS","CPT","CPB","COF","CAH","CCL","CARR","CVNA","CASY",
    "CAT","CBOE","CBRE","CDW","COR","CNC","CNP","CF","CRL","SCHW",
    "CHTR","CVX","CMG","CB","CHD","CIEN","CI","CINF","CTAS","CSCO",
    "C","CFG","CLX","CME","CMS","KO","CTSH","COHR","COIN","CL",
    "CMCSA","FIX","CAG","COP","ED","STZ","CEG","COO","CPRT","GLW",
    "CPAY","CTVA","CSGP","COST","CRH","CRWD","CCI","CSX","CMI","CVS",
    "DHR","DRI","DDOG","DVA","DECK","DE","DELL","DAL","DVN","DXCM",
    "FANG","DLR","DG","DLTR","D","DPZ","DASH","DOV","DOW","DHI",
    "DTE","DUK","DD","ETN","EBAY","SATS","ECL","EIX","EW","EA",
    "ELV","EME","EMR","ETR","EOG","EPAM","EQT","EFX","EQIX","EQR",
    "ERIE","ESS","EL","EG","EVRG","ES","EXC","EXE","EXPE","EXPD",
    "EXR","XOM","FFIV","FDS","FICO","FAST","FRT","FDX","FIS","FITB",
    "FSLR","FE","FISV","F","FTNT","FTV","FOXA","FOX","BEN","FCX",
    "GRMN","IT","GE","GEHC","GEV","GEN","GNRC","GD","GIS","GM",
    "GPC","GILD","GPN","GL","GDDY","GS","HAL","HIG","HAS","HCA",
    "DOC","HSIC","HSY","HPE","HLT","HD","HON","HRL","HST","HWM",
    "HPQ","HUBB","HUM","HBAN","HII","IBM","IEX","IDXX","ITW","INCY",
    "IR","PODD","INTC","IBKR","ICE","IFF","IP","INTU","ISRG","IVZ",
    "INVH","IQV","IRM","JBHT","JBL","JKHY","J","JNJ","JCI","JPM",
    "KVUE","KDP","KEY","KEYS","KMB","KIM","KMI","KKR","KLAC","KHC",
    "KR","LHX","LH","LRCX","LVS","LDOS","LEN","LII","LLY","LIN",
    "LYV","LMT","L","LOW","LULU","LITE","LYB","MTB","MPC","MAR",
    "MRSH","MLM","MAS","MA","MKC","MCD","MCK","MDT","MRK","META",
    "MET","MTD","MGM","MCHP","MU","MSFT","MAA","MRNA","TAP","MDLZ",
    "MPWR","MNST","MCO","MS","MOS","MSI","MSCI","NDAQ","NTAP","NFLX",
    "NEM","NWSA","NWS","NEE","NKE","NI","NDSN","NSC","NTRS","NOC",
    "NCLH","NRG","NUE","NVDA","NVR","NXPI","ORLY","OXY","ODFL","OMC",
    "ON","OKE","ORCL","OTIS","PCAR","PKG","PLTR","PANW","PSKY","PH",
    "PAYX","PYPL","PNR","PEP","PFE","PCG","PM","PSX","PNW","PNC",
    "POOL","PPG","PPL","PFG","PG","PGR","PLD","PRU","PEG","PTC",
    "PSA","PHM","PWR","QCOM","DGX","Q","RL","RJF","RTX","O",
    "REG","REGN","RF","RSG","RMD","RVTY","HOOD","ROK","ROL","ROP",
    "ROST","RCL","SPGI","CRM","SNDK","SBAC","SLB","STX","SRE","NOW",
    "SHW","SPG","SWKS","SJM","SW","SNA","SOLV","SO","LUV","SWK",
    "SBUX","STT","STLD","STE","SYK","SMCI","SYF","SNPS","SYY","TMUS",
    "TROW","TTWO","TPR","TRGP","TGT","TEL","TDY","TER","TSLA","TXN",
    "TPL","TXT","TMO","TJX","TKO","TTD","TSCO","TT","TDG","TRV",
    "TRMB","TFC","TYL","TSN","USB","UBER","UDR","ULTA","UNP","UAL",
    "UPS","URI","UNH","UHS","VLO","VEEV","VTR","VLTO","VRSN","VRSK",
    "VZ","VRTX","VRT","VTRS","VICI","V","VST","VMC","WRB","GWW",
    "WAB","WMT","DIS","WBD","WM","WAT","WEC","WFC","WELL","WST",
    "WDC","WY","WSM","WMB","WTW","WDAY","WYNN","XEL","XYL","YUM",
    "ZBRA","ZBH","ZTS","BLDR","POOL","ARE","IT","FDS","AMTM","EPAM",
    "CPB","TAP","CAG",
]

# ══ ת"א 125 ══
WATCHLIST_IL = [
    "TEVA.TA","NICE.TA","CHKP.TA","MNDY.TA","WIX.TA","GLBE.TA",
    "ICL.TA","ESLT.TA","AMOT.TA","MGDL.TA","HARL.TA","PHOE.TA",
    "DSCT.TA","LUMI.TA","POLI.TA","MZRH.TA","FIBI.TA","ITRN.TA",
    "ENLT.TA","SPEN.TA","CAMT.TA","CRNT.TA","NVMI.TA","RDRD.TA",
    "TSEM.TA","SMDR.TA","SKBN.TA","PRGO.TA","GILT.TA","STRS.TA",
    "ALHE.TA","AZRG.TA","BONS.TA","BWAY.TA","CPTP.TA","DGNS.TA",
    "DORL.TA","EMTC.TA","ENRG.TA","EVGN.TA","FTAL.TA","GISH.TA",
    "HDST.TA","ILCO.TA","ILEX.TA","ISCD.TA","KARE.TA","KRUR.TA",
    "LSCO.TA","MGOR.TA","MISH.TA","MLSR.TA","NETO.TA","NFTA.TA",
    "OBAS.TA","ORAD.TA","ORMP.TA","PLSN.TA","PTBL.TA","RSEL.TA",
    "SANO.TA","SPCE.TA","SUUR.TA","TACT.TA","TDRN.TA","TLSY.TA",
    "TZNR.TA","ULTR.TA","UNVO.TA","VTNA.TA","WLFL.TA","YAAK.TA",
    "ADGR.TA","AICS.TA","ALLT.TA","ARAD.TA","ARYT.TA","ASHO.TA",
    "AVIV.TA","BRAM.TA","BRIL.TA","CLIS.TA","DIFI.TA","DNYA.TA",
    "ELCO.TA","FROG.TA","GCMT.TA","GDEV.TA","GOVN.TA","IFON.TA",
    "IGLD.TA","INRM.TA","ISCO.TA","ISOP.TA","ISRA.TA","JBNK.TA",
    "KMDA.TA","KNFM.TA","MCRM.TA","MGIC.TA","MIGI.TA","MNIN.TA",
    "MRAN.TA","MSBI.TA","MTRX.TA","MVNE.TA","MZOR.TA","NILI.TA",
    "RFEL.TA","CLLI.TA","ORAN.TA","PERI.TA",
]


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
        tickers = WATCHLIST_IL
        label   = "ת\"א 125"
    elif market == "US":
        tickers = list(dict.fromkeys(WATCHLIST_NASDAQ + WATCHLIST_SP500))
        label   = "נאסד\"ק 100 + S&P 500"
    else:
        tickers = list(dict.fromkeys(
            WATCHLIST_IL + WATCHLIST_NASDAQ + WATCHLIST_SP500
        ))
        label = "כל השווקים"

    print(f"\nסורק {label} — {len(tickers)} מניות...")

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

        special = False
        try:
            hist_1y = yf.download(ticker, period="1y", interval="1d",
                                  progress=False, auto_adjust=True)
            special = check_special_conditions(data, hist_1y)
            if special:
                ts += 15
        except:
            pass

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
            "special":     special,
            "rec":         "כניסה" if s >= 60 else "המתן",
        })

        time.sleep(0.5)  # מניעת חסימה

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