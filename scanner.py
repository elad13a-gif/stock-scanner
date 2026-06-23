import yfinance as yf
import pandas as pd
import ta
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
 
STOP_LOSS = 0.03
TARGET    = 0.05
 
# ══ נאסד"ק 100 — רשימה רשמית יוני 2026 ══
WATCHLIST_NASDAQ = [
    "NVDA","AAPL","MSFT","AMZN","GOOGL","GOOG","AVGO","TSLA","META","MU",
    "WMT","AMD","ASML","INTC","LRCX","AMAT","CSCO","ARM","COST","KLAC",
    "SNDK","NFLX","TXN","PLTR","MRVL","WDC","STX","LIN","QCOM","PANW",
    "ADI","TMUS","PEP","AMGN","CRWD","APP","GILD","HON","ISRG","SHOP",
    "BKNG","VRTX","SBUX","PDD","CDNS","FTNT","MAR","CEG","MNST","SNPS",
    "CSX","ADP","ABNB","NXPI","MELI","CMCSA","DDOG","ADBE","MDLZ","ROST",
    "MPWR","ALAB","DASH","NBIS","TER","ORLY","AEP","INTU","LITE","CTAS",
    "WBD","REGN","PCAR","RKLB","CRWV","BKR","MCHP","FAST","FANG","EA",
    "FER","XEL","EXC","ODFL","TTWO","IDXX","CCEP","KDP","ADSK","MSTR",
    "ALNY","PYPL","PAYX","TRI","AXON","ROP","WDAY","GEHC","CPRT","DXCM",
    "KHC",
]
 
# ══ S&P 500 — רשימה רשמית יוני 2026 ══
WATCHLIST_SP500 = [
    "NVDA","AAPL","MSFT","AMZN","GOOGL","GOOG","AVGO","TSLA","META","MU",
    "BRK.B","LLY","WMT","JPM","AMD","INTC","V","XOM","JNJ","ORCL",
    "LRCX","AMAT","CSCO","CAT","MA","COST","ABBV","BAC","GE","UNH",
    "MS","KLAC","CVX","PG","KO","SNDK","HD","GS","NFLX","GEV",
    "TXN","PLTR","MRK","PM","DELL","MRVL","WFC","WDC","C","STX",
    "RTX","QCOM","LIN","PANW","IBM","AXP","ANET","ADI","APH","TMUS",
    "PEP","MCD","VZ","AMGN","TJX","NEE","DIS","GLW","BA","CRWD",
    "TMO","ETN","BLK","DE","SCHW","UNP","APP","GILD","T","ABT",
    "BX","WELL","UBER","HON","PFE","ISRG","VRT","PLD","COP","CVS",
    "BKNG","DHR","CB","COF","PGR","CRM","PH","LOW","SPGI","VRTX",
    "SYK","MO","SBUX","LMT","HWM","BMY","EQIX","PWR","TT","NEM",
    "SO","FTNT","CDNS","MAR","MDT","CMI","BNY","FCX","CEG","DUK",
    "HOOD","NOW","PNC","GD","UPS","WMB","USB","MNST","JCI","CME",
    "MCK","KKR","SNPS","ADP","WM","ELV","CSX","MMM","EMR","RCL",
    "HCA","AMT","COHR","ABNB","NXPI","CMCSA","SHW","FDX","APO","MCO",
    "HLT","MRSH","DDOG","MDLZ","ADBE","ITW","ROST","DASH","ECL","MPWR",
    "CI","CRH","ICE","ACN","GM","TDG","NOC","MPC","CL","FIX",
    "VLO","KMI","SLB","ORLY","AEP","EOG","TER","INTU","SPG","LITE",
    "DLR","NSC","URI","CTAS","PSX","AON","WBD","TRV","MSI","BSX",
    "NKE","HPE","REGN","GWW","KEYS","PCAR","APD","CIEN","RSG","TEL",
    "TFC","D","SRE","CARR","AFL","TGT","BKR","ALL","O","F",
    "DAL","PSA","VST","MET","TRGP","NUE","MCHP","FLEX","AME","OKE",
    "AJG","FAST","ROK","LHX","COR","FANG","CTVA","CAH","OXY","ETR",
    "ON","EA","DVN","EW","XEL","FITB","CVNA","AZO","STT","EXC",
    "EBAY","WAB","NDAQ","ODFL","GRMN","DHI","TTWO","XYZ","IDXX","COIN",
    "IBKR","HUM","AMP","KDP","CCL","MSCI","YUM","AIG","VTR","PEG",
    "LYV","CMG","ED","IRM","VMC","ADSK","JBL","BDX","UAL","CBRE",
    "EME","PRU","SYY","PYPL","WEC","MLM","PCG","CCI","ADM","STLD",
    "A","HIG","WAT","HSY","PAYX","KVUE","HBAN","KR","KMB","MTB",
    "ROP","AXON","NTRS","ZTS","ACGL","EQT","LVS","CNC","EXR","NTAP",
    "CASY","EL","DOV","DTE","RJF","IR","SATS","AEE","TPR","BIIB",
    "HAL","NRG","CFG","ARES","EXPE","TDY","FSLR","CNP","ATO","VICI",
    "HUBB","IQV","OTIS","WDAY","EIX","GEHC","RMD","CPRT","FE","PPL",
    "WSM","PPG","CINF","CBOE","DXCM","XYL","KHC","ES","JBHT","AVB",
    "SYF","FISV","DG","WRB","FICO","VEEV","FDXF","KEY","STZ","AWK",
    "RF","DRI","RL","TPL","EQR","PFG","LUV","PHM","WTW","MRNA",
    "SW","TROW","MTD","WST","CMS","NI","SMCI","CPAY","VRSN","CHD",
    "DOW","CHRW","L","DLTR","VRSK","FFIV","HPQ","BG","DGX","LEN",
    "EXPD","ROL","EXE","LH","PKG","OMC","INCY","VLTO","SNA","SBAC",
    "BRO","IP","ULTA","CTSH","TSN","IFF","STE","DD","FIS","EVRG",
    "LNT","AMCR","FTV","LYB","LII","ALB","EFX","GPN","GIS","WY",
    "VTRS","ESS","BEN","AKAM","NVR","HST","GNRC","ZBH","INVH","KIM",
    "IEX","NDSN","BBY","CDW","CF","BR","TSCO","BALL","MAA","CHTR",
    "TXT","TKO","MAS","DECK","GPC","J","REG","DOC","DVA","GEN",
    "APTV","SWK","GL","EG","HRL","PTC","AIZ","LDOS","COO","SOLV",
    "IVZ","ALGN","BF.B","PNW","MKC","UDR","AVY","APA","PNR","CSGP",
    "HAS","LULU","MGM","SWKS","ZBRA","SJM","TRMB","TYL","ALLE","ERIE",
    "CLX","RVTY","PSKY","HII","CPT","WYNN","FRT","AES","BXP","BAX",
    "DPZ","FOX","GDDY","PODD","FOXA","NCLH","HSIC","NWSA","NWS",
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
 
 
# ─── סריקה מקבילית ────────────────────────────────────
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
    return {
        **data,
        "score":       s,
        "invest":      amt,
        "shares":      max(1, int(amt // data["price"])),
        "stop":        round(data["price"] * (1 - STOP_LOSS), 2),
        "target":      round(data["price"] * (1 + TARGET), 2),
        "maya_events": maya_events,
        "special":     special,
        "rec":         "כניסה" if s >= 60 else "המתן",
    }
 
 
# ─── סריקה ראשית ──────────────────────────────────────
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
 
    with ThreadPoolExecutor(max_workers=8) as ex:
        raw = list(ex.map(scan_one, tickers))
 
    results = [r for r in raw if r]
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
 