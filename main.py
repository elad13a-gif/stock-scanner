import schedule
import time
import threading
import requests
import json
from scanner import run_scan
from notify import send, format_message
from tracker import add_recommendation, run_tracker
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from scanner import analyze, tech_score, position, get_maya_events, STOP_LOSS, TARGET
import pytz
from datetime import datetime

TOKEN   = "8931673908:AAEAkLdaMDSobsY8VOO8gOsTPZzf7mBLy2E"
CHAT_ID = "840664684"

# ══════════════════════════════════════════════════════
# מילון שמות מניות — מובנה בקוד, לא תלוי בקובץ חיצוני
# ══════════════════════════════════════════════════════
STOCK_NAMES = {
    # נאסד"ק 100
    "nvda":"NVDA","nvidia":"NVDA","נווידיה":"NVDA","אינבידיה":"NVDA","אנווידיה":"NVDA",
    "goog":"GOOG","googl":"GOOGL","google":"GOOGL","גוגל":"GOOGL","alphabet":"GOOGL","אלפבית":"GOOGL",
    "aapl":"AAPL","apple":"AAPL","אפל":"AAPL",
    "msft":"MSFT","microsoft":"MSFT","מייקרוסופט":"MSFT","מיקרוסופט":"MSFT",
    "amzn":"AMZN","amazon":"AMZN","אמזון":"AMZN",
    "avgo":"AVGO","broadcom":"AVGO","ברודקום":"AVGO",
    "tsla":"TSLA","tesla":"TSLA","טסלה":"TSLA",
    "meta":"META","facebook":"META","פייסבוק":"META","מטא":"META",
    "mu":"MU","micron":"MU","מיקרון":"MU",
    "wmt":"WMT","walmart":"WMT","וולמארט":"WMT",
    "amd":"AMD","advanced micro devices":"AMD","אי אם די":"AMD",
    "asml":"ASML","אסמל":"ASML",
    "intc":"INTC","intel":"INTC","אינטל":"INTC",
    "csco":"CSCO","cisco":"CSCO","סיסקו":"CSCO",
    "cost":"COST","costco":"COST","קוסטקו":"COST",
    "lrcx":"LRCX","lam research":"LRCX","לאם":"LRCX",
    "arm":"ARM","ארם":"ARM",
    "pltr":"PLTR","palantir":"PLTR","פלנטיר":"PLTR",
    "amat":"AMAT","applied materials":"AMAT","אפלייד":"AMAT",
    "nflx":"NFLX","netflix":"NFLX","נטפליקס":"NFLX",
    "txn":"TXN","texas instruments":"TXN","טקסס אינסטרומנטס":"TXN",
    "qcom":"QCOM","qualcomm":"QCOM","קוואלקום":"QCOM",
    "klac":"KLAC","kla":"KLAC",
    "lin":"LIN","linde":"LIN","לינדה":"LIN",
    "panw":"PANW","palo alto":"PANW","פאלו אלטו":"PANW",
    "adi":"ADI","analog devices":"ADI","אנלוג":"ADI",
    "stx":"STX","seagate":"STX","סיגייט":"STX",
    "tmus":"TMUS","t-mobile":"TMUS","טי מובייל":"TMUS",
    "pep":"PEP","pepsi":"PEP","pepsico":"PEP","פפסי":"PEP",
    "app":"APP","applovin":"APP","אפליוין":"APP",
    "wdc":"WDC","western digital":"WDC","ווסטרן דיגיטל":"WDC",
    "amgn":"AMGN","amgen":"AMGN","אמג'ן":"AMGN",
    "crwd":"CRWD","crowdstrike":"CRWD","קראודסטרייק":"CRWD",
    "mrvl":"MRVL","marvell":"MRVL","מרוול":"MRVL",
    "gild":"GILD","gilead":"GILD","גילאד":"GILD",
    "isrg":"ISRG","intuitive surgical":"ISRG","אינטואיטיב":"ISRG",
    "shop":"SHOP","shopify":"SHOP","שופיפיי":"SHOP",
    "hon":"HON","honeywell":"HON","האניוול":"HON",
    "bkng":"BKNG","booking":"BKNG","בוקינג":"BKNG",
    "pdd":"PDD","temu":"PDD","טמו":"PDD",
    "sbux":"SBUX","starbucks":"SBUX","סטארבקס":"SBUX",
    "vrtx":"VRTX","vertex":"VRTX","ורטקס":"VRTX",
    "ceg":"CEG","constellation energy":"CEG",
    "cdns":"CDNS","cadence":"CDNS","קדנס":"CDNS",
    "mar":"MAR","marriott":"MAR","מריוט":"MAR",
    "adbe":"ADBE","adobe":"ADBE","אדובי":"ADBE",
    "ftnt":"FTNT","fortinet":"FTNT","פורטינט":"FTNT",
    "snps":"SNPS","synopsys":"SNPS","סינופסיס":"SNPS",
    "cmcsa":"CMCSA","comcast":"CMCSA","קומקאסט":"CMCSA",
    "adp":"ADP","automatic data processing":"ADP",
    "intu":"INTU","intuit":"INTU","אינטואיט":"INTU",
    "meli":"MELI","mercado libre":"MELI","מרקדו":"MELI",
    "mnst":"MNST","monster":"MNST","מונסטר":"MNST",
    "csx":"CSX",
    "nxpi":"NXPI","nxp":"NXPI",
    "ddog":"DDOG","datadog":"DDOG","דאטאדוג":"DDOG",
    "mpwr":"MPWR","monolithic power":"MPWR",
    "abnb":"ABNB","airbnb":"ABNB","אירביאנבי":"ABNB",
    "mdlz":"MDLZ","mondelez":"MDLZ","מונדלז":"MDLZ",
    "rost":"ROST","ross stores":"ROST",
    "orly":"ORLY","o'reilly":"ORLY","אוריילי":"ORLY",
    "dash":"DASH","doordash":"DASH","דורדאש":"DASH",
    "aep":"AEP","american electric power":"AEP",
    "ctas":"CTAS","cintas":"CTAS",
    "wbd":"WBD","warner bros":"WBD","וורנר":"WBD",
    "bkr":"BKR","baker hughes":"BKR",
    "regn":"REGN","regeneron":"REGN","ריג'נרון":"REGN",
    "pcar":"PCAR","paccar":"PCAR",
    "fang":"FANG","diamondback":"FANG",
    "mstr":"MSTR","microstrategy":"MSTR","strategy":"MSTR","מיקרוסטרטג'י":"MSTR",
    "mchp":"MCHP","microchip":"MCHP","מיקרוצ'יפ":"MCHP",
    "fast":"FAST","fastenal":"FAST",
    "ea":"EA","electronic arts":"EA","אלקטרוניק ארטס":"EA",
    "xel":"XEL","xcel energy":"XEL",
    "fer":"FER","ferrovial":"FER",
    "odfl":"ODFL","old dominion":"ODFL",
    "exc":"EXC","exelon":"EXC",
    "adsk":"ADSK","autodesk":"ADSK","אוטודסק":"ADSK",
    "idxx":"IDXX","idexx":"IDXX",
    "ttwo":"TTWO","take-two":"TTWO","take two":"TTWO","טייק טו":"TTWO",
    "ccep":"CCEP","coca-cola europacific":"CCEP",
    "kdp":"KDP","keurig dr pepper":"KDP",
    "alny":"ALNY","alnylam":"ALNY",
    "pypl":"PYPL","paypal":"PYPL","פייפאל":"PYPL",
    "tri":"TRI","thomson reuters":"TRI",
    "payx":"PAYX","paychex":"PAYX",
    "axon":"AXON","axon enterprise":"AXON","טייזר":"AXON",
    "wday":"WDAY","workday":"WDAY","וורקדיי":"WDAY",
    "rop":"ROP","roper":"ROP",
    "cprt":"CPRT","copart":"CPRT",
    "khc":"KHC","kraft heinz":"KHC","קראפט היינץ":"KHC",
    "gehc":"GEHC","ge healthcare":"GEHC",
    "dxcm":"DXCM","dexcom":"DXCM","דקסקום":"DXCM",
    "ctsh":"CTSH","cognizant":"CTSH","קוגניזנט":"CTSH",
    "team":"TEAM","atlassian":"TEAM","אטלסיאן":"TEAM",
    "insm":"INSM","insmed":"INSM",
    "vrsk":"VRSK","verisk":"VRSK",
    "zs":"ZS","zscaler":"ZS","זסקיילר":"ZS",
    "chtr":"CHTR","charter":"CHTR",
    "csgp":"CSGP","costar":"CSGP",
    "spcx":"SPCX","spacex":"SPCX","ספייסקס":"SPCX","ספייס אקס":"SPCX","חלל":"SPCX",
    # S&P 500
    "jpm":"JPM","jpmorgan":"JPM","jp morgan":"JPM","ג'יפי מורגן":"JPM",
    "bac":"BAC","bank of america":"BAC","בנק אמריקה":"BAC",
    "wfc":"WFC","wells fargo":"WFC","וולס פארגו":"WFC",
    "gs":"GS","goldman sachs":"GS","גולדמן":"GS",
    "ms":"MS","morgan stanley":"MS","מורגן סטנלי":"MS",
    "v":"V","visa":"V","ויזה":"V",
    "ma":"MA","mastercard":"MA","מאסטרקארד":"MA",
    "brk-b":"BRK-B","berkshire":"BRK-B","ברקשייר":"BRK-B","באפט":"BRK-B",
    "axp":"AXP","american express":"AXP","אמריקן אקספרס":"AXP",
    "c":"C","citigroup":"C","סיטי":"C",
    "blk":"BLK","blackrock":"BLK","בלאקרוק":"BLK",
    "schw":"SCHW","schwab":"SCHW","שוואב":"SCHW",
    "usb":"USB","us bancorp":"USB",
    "pnc":"PNC","pnc financial":"PNC",
    "cof":"COF","capital one":"COF","קפיטל וואן":"COF",
    "spgi":"SPGI","s&p global":"SPGI",
    "mco":"MCO","moody's":"MCO","מודיס":"MCO",
    "lly":"LLY","eli lilly":"LLY","lilly":"LLY","אלי לילי":"LLY",
    "jnj":"JNJ","johnson":"JNJ","ג'ונסון":"JNJ",
    "unh":"UNH","unitedhealth":"UNH","יונייטד הלת'":"UNH",
    "abbv":"ABBV","abbvie":"ABBV","אבווי":"ABBV",
    "pfe":"PFE","pfizer":"PFE","פייזר":"PFE",
    "mrk":"MRK","merck":"MRK","מרק":"MRK",
    "bmy":"BMY","bristol myers":"BMY","בריסטול":"BMY",
    "cvs":"CVS","cvs health":"CVS",
    "ci":"CI","cigna":"CI","סיגנה":"CI",
    "hum":"HUM","humana":"HUM",
    "elv":"ELV","elevance":"ELV",
    "hca":"HCA","hca healthcare":"HCA",
    "tmo":"TMO","thermo fisher":"TMO","תרמו פישר":"TMO",
    "dhr":"DHR","danaher":"DHR",
    "abt":"ABT","abbott":"ABT","אבוט":"ABT",
    "syk":"SYK","stryker":"SYK","סטרייקר":"SYK",
    "bsx":"BSX","boston scientific":"BSX",
    "mdt":"MDT","medtronic":"MDT","מדטרוניק":"MDT",
    "xom":"XOM","exxon":"XOM","אקסון":"XOM",
    "cvx":"CVX","chevron":"CVX","שברון":"CVX",
    "cop":"COP","conocophillips":"COP",
    "slb":"SLB","schlumberger":"SLB","שלמברגר":"SLB",
    "hal":"HAL","halliburton":"HAL","הליברטון":"HAL",
    "oxy":"OXY","occidental":"OXY","אוקסידנטל":"OXY",
    "eog":"EOG","eog resources":"EOG",
    "psx":"PSX","phillips 66":"PSX",
    "vlo":"VLO","valero":"VLO","ולרו":"VLO",
    "ge":"GE","general electric":"GE","ג'נרל אלקטריק":"GE",
    "cat":"CAT","caterpillar":"CAT","קטרפילר":"CAT",
    "ba":"BA","boeing":"BA","בואינג":"BA",
    "rtx":"RTX","raytheon":"RTX","רייתיאון":"RTX",
    "lmt":"LMT","lockheed":"LMT","לוקהיד":"LMT",
    "noc":"NOC","northrop":"NOC","נורת'רופ":"NOC",
    "gd":"GD","general dynamics":"GD","ג'נרל דיינמיקס":"GD",
    "mmm":"MMM","3m":"MMM","תלת אם":"MMM",
    "emr":"EMR","emerson":"EMR",
    "etn":"ETN","eaton":"ETN","איטון":"ETN",
    "de":"DE","deere":"DE","ג'ון דיר":"DE","john deere":"DE",
    "unp":"UNP","union pacific":"UNP",
    "ups":"UPS","united parcel":"UPS","יו פי אס":"UPS",
    "hd":"HD","home depot":"HD","הום דיפו":"HD",
    "low":"LOW","lowe's":"LOW","לואוס":"LOW",
    "tgt":"TGT","target":"TGT","טארגט":"TGT",
    "mcd":"MCD","mcdonald's":"MCD","מקדונלדס":"MCD",
    "nke":"NKE","nike":"NKE","נייקי":"NKE",
    "tjx":"TJX","tjx companies":"TJX",
    "ko":"KO","coca cola":"KO","קוקה קולה":"KO","coke":"KO",
    "pg":"PG","procter gamble":"PG","פרוקטר וגמבל":"PG",
    "pm":"PM","philip morris":"PM","פיליפ מוריס":"PM",
    "mo":"MO","altria":"MO","אלטריה":"MO",
    "dis":"DIS","disney":"DIS","דיסני":"DIS",
    "orcl":"ORCL","oracle":"ORCL","אורקל":"ORCL",
    "crm":"CRM","salesforce":"CRM","סיילספורס":"CRM",
    "ibm":"IBM","איי בי אם":"IBM",
    "now":"NOW","servicenow":"NOW","סרביס נאו":"NOW",
    "acn":"ACN","accenture":"ACN","אקסנצ'ר":"ACN",
    "anet":"ANET","arista":"ANET","אריסטה":"ANET",
    "dell":"DELL","dell technologies":"DELL","דל":"DELL",
    "bx":"BX","blackstone":"BX","בלאקסטון":"BX",
    "kkr":"KKR","kkr & co":"KKR",
    "cb":"CB","chubb":"CB","צ'אב":"CB",
    "pgr":"PGR","progressive":"PGR","פרוגרסיב":"PGR",
    "trv":"TRV","travelers":"TRV","טרוולרס":"TRV",
    "all":"ALL","allstate":"ALL","אולסטייט":"ALL",
    "met":"MET","metlife":"MET","מטלייף":"MET",
    "pru":"PRU","prudential":"PRU","פרודנשל":"PRU",
    "afl":"AFL","aflac":"AFL","אפלאק":"AFL",
    "nee":"NEE","nextera":"NEE","נקסט אירה":"NEE",
    "duk":"DUK","duke energy":"DUK","דיוק":"DUK",
    "so":"SO","southern company":"SO","סאת'רן":"SO",
    "d":"D","dominion":"D","דומיניון":"D",
    "sre":"SRE","sempra":"SRE","סמפרה":"SRE",
    "amt":"AMT","american tower":"AMT","אמריקן טאואר":"AMT",
    "pld":"PLD","prologis":"PLD","פרולוג'יס":"PLD",
    "cci":"CCI","crown castle":"CCI","קראון קאסל":"CCI",
    "eqix":"EQIX","equinix":"EQIX","אקווינקס":"EQIX",
    "psa":"PSA","public storage":"PSA",
    "well":"WELL","welltower":"WELL",
    "vrt":"VRT","vertiv":"VRT","ורטיב":"VRT",
    "pwr":"PWR","quanta services":"PWR","קוואנטה":"PWR",
    "nem":"NEM","newmont":"NEM","ניומונט":"NEM","זהב":"NEM",
    "fcx":"FCX","freeport":"FCX","פריפורט":"FCX","נחושת":"FCX",
    "apd":"APD","air products":"APD",
    "ecl":"ECL","ecolab":"ECL",
    "shw":"SHW","sherwin williams":"SHW","שרווין":"SHW",
    "mck":"MCK","mckesson":"MCK",
    "cah":"CAH","cardinal health":"CAH",
    "uber":"UBER","אובר":"UBER",
    "lyft":"LYFT","ליפט":"LYFT",
    "coin":"COIN","coinbase":"COIN","קוינבייס":"COIN",
    "snow":"SNOW","snowflake":"SNOW","סנואופלייק":"SNOW",
    "mdb":"MDB","mongodb":"MDB","מונגו":"MDB",
    "net":"NET","cloudflare":"NET","קלאודפלייר":"NET",
    "okta":"OKTA","אוקטה":"OKTA",
    "zm":"ZM","zoom":"ZM","זום":"ZM",
    "gev":"GEV","ge vernova":"GEV",
    "tt":"TT","trane":"TT","טריין":"TT",
    "jci":"JCI","johnson controls":"JCI",
    "wmb":"WMB","williams":"WMB",
    "wm":"WM","waste management":"WM","פסולת":"WM",
    "nsc":"NSC","norfolk southern":"NSC","נורפולק":"NSC",
    "zts":"ZTS","zoetis":"ZTS",
    "aon":"AON","אאון":"AON",
    "mmc":"MMC","marsh":"MMC","מארש":"MMC",
    "dks":"DKS","dick's sporting":"DKS","דיקס":"DKS",
    "cmg":"CMG","chipotle":"CMG","צ'יפוטלה":"CMG",
    "yum":"YUM","yum brands":"YUM","יאם":"YUM",
    "dri":"DRI","darden":"DRI",
    "hlt":"HLT","hilton":"HLT","הילטון":"HLT",
    "azn":"AZN","astrazeneca":"AZN","אסטרה":"AZN",
    "nvo":"NVO","novo nordisk":"NVO","נובו נורדיסק":"NVO","אוזמפיק":"NVO",
    "gsk":"GSK","glaxo":"GSK","גלאקסו":"GSK",
    "sny":"SNY","sanofi":"SNY","סנופי":"SNY",
    "biib":"BIIB","biogen":"BIIB","ביוג'ן":"BIIB",
    "ilmn":"ILMN","illumina":"ILMN","אילומינה":"ILMN",
    "bntx":"BNTX","biontech":"BNTX","ביואנטק":"BNTX",
    "mrna":"MRNA","moderna":"MRNA","מודרנה":"MRNA",
    "wat":"WAT","waters":"WAT",
    "ntra":"NTRA","natera":"NTRA","נטרה":"NTRA",
    "rga":"RGA","reinsurance group":"RGA",
    # ת"א 125
    "teva":"TEVA.TA","טבע":"TEVA.TA","תבע":"TEVA.TA",
    "nice":"NICE.TA","נייס":"NICE.TA",
    "chkp":"CHKP.TA","checkpoint":"CHKP.TA","צ'ק פוינט":"CHKP.TA","check point":"CHKP.TA",
    "mndy":"MNDY.TA","monday":"MNDY.TA","מאנדיי":"MNDY.TA","monday.com":"MNDY.TA",
    "wix":"WIX.TA","וויקס":"WIX.TA","ויקס":"WIX.TA",
    "glbe":"GLBE.TA","global-e":"GLBE.TA","גלובל-e":"GLBE.TA","גלובל אי":"GLBE.TA",
    "icl":"ICL.TA","כיל":"ICL.TA","israel chemicals":"ICL.TA",
    "eslt":"ESLT.TA","אלביט":"ESLT.TA","elbit":"ESLT.TA","elbit systems":"ESLT.TA","אלביט מערכות":"ESLT.TA",
    "amot":"AMOT.TA","עמות":"AMOT.TA",
    "mgdl":"MGDL.TA","מגדל":"MGDL.TA","migdal":"MGDL.TA","מגדל ביטוח":"MGDL.TA",
    "harl":"HARL.TA","הראל":"HARL.TA","harel":"HARL.TA","הראל ביטוח":"HARL.TA",
    "phoe":"PHOE.TA","פניקס":"PHOE.TA","phoenix":"PHOE.TA","הפניקס":"PHOE.TA",
    "dsct":"DSCT.TA","דיסקונט":"DSCT.TA","discount":"DSCT.TA","בנק דיסקונט":"DSCT.TA",
    "lumi":"LUMI.TA","לאומי":"LUMI.TA","leumi":"LUMI.TA","בנק לאומי":"LUMI.TA",
    "poli":"POLI.TA","פועלים":"POLI.TA","hapoalim":"POLI.TA","בנק הפועלים":"POLI.TA",
    "mzrh":"MZRH.TA","מזרחי":"MZRH.TA","mizrahi":"MZRH.TA","מזרחי טפחות":"MZRH.TA",
    "fibi":"FIBI.TA","הבינלאומי":"FIBI.TA","first international":"FIBI.TA","הבנק הבינלאומי":"FIBI.TA",
    "itrn":"ITRN.TA","אינטרן":"ITRN.TA","ituran":"ITRN.TA",
    "enlt":"ENLT.TA","אנלייט":"ENLT.TA","enlight":"ENLT.TA",
    "spen":"SPEN.TA","שופרסל":"SPEN.TA","shufersal":"SPEN.TA",
    "camt":"CAMT.TA","קמטק":"CAMT.TA","camtek":"CAMT.TA",
    "crnt":"CRNT.TA","קרנט":"CRNT.TA","ceragon":"CRNT.TA",
    "nvmi":"NVMI.TA","נובה":"NVMI.TA","nova":"NVMI.TA",
    "rdrd":"RDRD.TA","רד-רד":"RDRD.TA",
    "tsem":"TSEM.TA","טאוור":"TSEM.TA","tower":"TSEM.TA","tower semiconductor":"TSEM.TA","טאוור סמיקונדקטור":"TSEM.TA",
    "smdr":"SMDR.TA","סמדר":"SMDR.TA",
    "skbn":"SKBN.TA","סקייליין":"SKBN.TA",
    "prgo":"PRGO.TA","פרגו":"PRGO.TA","perrigo":"PRGO.TA",
    "gilt":"GILT.TA","גילת":"GILT.TA","gilat":"GILT.TA",
    "strs":"STRS.TA","סטרוס":"STRS.TA","strauss":"STRS.TA",
    "alhe":"ALHE.TA","אלה":"ALHE.TA",
    "azrg":"AZRG.TA","עזריאלי":"AZRG.TA","azrieli":"AZRG.TA","קבוצת עזריאלי":"AZRG.TA",
    "bway":"BWAY.TA","ביווי":"BWAY.TA",
    "dgns":"DGNS.TA","דיגנוסטיקס":"DGNS.TA",
    "dorl":"DORL.TA","דורל":"DORL.TA",
    "evgn":"EVGN.TA","אוורגרין":"EVGN.TA","evogene":"EVGN.TA",
    "ftal":"FTAL.TA","פטל":"FTAL.TA",
    "gish":"GISH.TA","גיש":"GISH.TA",
    "hdst":"HDST.TA","הדסת":"HDST.TA",
    "ilco":"ILCO.TA","ילקו":"ILCO.TA",
    "ilex":"ILEX.TA","אילקס":"ILEX.TA",
    "iscd":"ISCD.TA","ישרקארד":"ISCD.TA","isracard":"ISCD.TA",
    "kare":"KARE.TA","קארה":"KARE.TA",
    "krur":"KRUR.TA","קרור":"KRUR.TA",
    "lsco":"LSCO.TA","לסקו":"LSCO.TA",
    "mgor":"MGOR.TA","מגור":"MGOR.TA",
    "mish":"MISH.TA","מישלב":"MISH.TA",
    "mlsr":"MLSR.TA","מלסר":"MLSR.TA",
    "neto":"NETO.TA","נטו":"NETO.TA",
    "nfta":"NFTA.TA","נפטא":"NFTA.TA",
    "obas":"OBAS.TA","עובד באס":"OBAS.TA",
    "orad":"ORAD.TA","אוראד":"ORAD.TA",
    "plsn":"PLSN.TA","פלסן":"PLSN.TA",
    "ptbl":"PTBL.TA","פתאל":"PTBL.TA","fattal":"PTBL.TA","מלונות פתאל":"PTBL.TA",
    "rsel":"RSEL.TA","רסל":"RSEL.TA",
    "sano":"SANO.TA","סנו":"SANO.TA",
    "suur":"SUUR.TA","שור":"SUUR.TA",
    "tact":"TACT.TA","טאקט":"TACT.TA",
    "tdrn":"TDRN.TA","טדיראן":"TDRN.TA","tadiran":"TDRN.TA",
    "tlsy":"TLSY.TA","תלסי":"TLSY.TA",
    "tznr":"TZNR.TA","טצנר":"TZNR.TA",
    "ultr":"ULTR.TA","אולטרה":"ULTR.TA","ultra":"ULTR.TA",
    "unvo":"UNVO.TA","אונבו":"UNVO.TA",
    "vtna":"VTNA.TA","ויטנה":"VTNA.TA",
    "wlfl":"WLFL.TA","וולפסון":"WLFL.TA",
    "yaak":"YAAK.TA","יעקב":"YAAK.TA",
    "adgr":"ADGR.TA","אדגר":"ADGR.TA","adgar":"ADGR.TA",
    "allt":"ALLT.TA","אלוט":"ALLT.TA","allot":"ALLT.TA",
    "arad":"ARAD.TA","ארד":"ARAD.TA",
    "aryt":"ARYT.TA","אריית":"ARYT.TA",
    "asho":"ASHO.TA","אשוח":"ASHO.TA",
    "aviv":"AVIV.TA","אביב":"AVIV.TA",
    "bram":"BRAM.TA","ברם":"BRAM.TA",
    "bril":"BRIL.TA","ברילנס":"BRIL.TA",
    "clis":"CLIS.TA","קליס":"CLIS.TA",
    "difi":"DIFI.TA","דיפי":"DIFI.TA",
    "dnya":"DNYA.TA","דניה":"DNYA.TA","danya":"DNYA.TA","דניה סיבוס":"DNYA.TA",
    "elco":"ELCO.TA","אלקו":"ELCO.TA",
    "frog":"FROG.TA","פרוג":"FROG.TA","jfrog":"FROG.TA","ג'יפרוג":"FROG.TA",
    "gcmt":"GCMT.TA","גלובל קומוניטי":"GCMT.TA",
    "gdev":"GDEV.TA","ג'ידב":"GDEV.TA",
    "govn":"GOVN.TA","גובן":"GOVN.TA",
    "ifon":"IFON.TA","סלקום":"IFON.TA","cellcom":"IFON.TA",
    "igld":"IGLD.TA","אייגולד":"IGLD.TA",
    "inrm":"INRM.TA","אינרם":"INRM.TA",
    "isco":"ISCO.TA","איסקו":"ISCO.TA",
    "isop":"ISOP.TA","איסופארם":"ISOP.TA",
    "isra":"ISRA.TA","ישרא":"ISRA.TA",
    "jbnk":"JBNK.TA","בנק ירושלים":"JBNK.TA",
    "kmda":"KMDA.TA","קמדה":"KMDA.TA","kamada":"KMDA.TA",
    "knfm":"KNFM.TA","קנפ מדיקל":"KNFM.TA",
    "mcrm":"MCRM.TA","מקרם":"MCRM.TA",
    "mgic":"MGIC.TA","מג'יק":"MGIC.TA","magic software":"MGIC.TA","מג'יק סופטוור":"MGIC.TA",
    "migi":"MIGI.TA","מיגי":"MIGI.TA",
    "mnin":"MNIN.TA","מינין":"MNIN.TA",
    "mran":"MRAN.TA","מראן":"MRAN.TA",
    "msbi":"MSBI.TA","מסבי":"MSBI.TA",
    "mtrx":"MTRX.TA","מטריקס":"MTRX.TA","matrix":"MTRX.TA",
    "mvne":"MVNE.TA","מבנה":"MVNE.TA",
    "mzor":"MZOR.TA","מזור":"MZOR.TA","mazor":"MZOR.TA",
    "nili":"NILI.TA","נילי":"NILI.TA",
    "rafael":"RFEL.TA","רפאל":"RFEL.TA",
    "clal":"CLLI.TA","כלל":"CLLI.TA","כלל ביטוח":"CLLI.TA",
}

# ─── סריקות ───────────────────────────────────────────
def scan_israel():
    print("🇮🇱 סריקת ת\"א 125...")
    try:
        recs = run_scan("IL")
        top  = [r for r in recs if r["score"] >= 90]
        if top:
            msg = "🇮🇱 10:00 — מניות עם ציון 90+\n\n" + format_message(top)
            add_recommendation(top)
        else:
            msg = "🇮🇱 10:00 — אין מניות עם ציון 90+ היום"
        send(msg)
    except Exception as e:
        print(f"שגיאה: {e}")

def scan_usa():
    print("🇺🇸 סריקת ארה\"ב...")
    try:
        recs = run_scan("US")
        top  = [r for r in recs if r["score"] >= 90]
        if top:
            msg = "🇺🇸 16:00 — מניות עם ציון 90+\n\n" + format_message(top)
            add_recommendation(top)
        else:
            msg = "🇺🇸 16:00 — אין מניות עם ציון 90+ היום"
        send(msg)
    except Exception as e:
        print(f"שגיאה: {e}")

def run_scheduler():
    tz = pytz.timezone("Asia/Jerusalem")

    def check_and_run():
        now     = datetime.now(tz)
        hour    = now.hour
        minute  = now.minute
        weekday = now.weekday()
        if weekday >= 5:
            return
        if hour == 10 and minute == 0:
            scan_israel()
        if hour == 16 and minute == 0:
            scan_usa()

    schedule.every().minute.do(check_and_run)
    print("✅ סורק פעיל! 10:00 ת\"א | 16:00 ארה\"ב")
    while True:
        schedule.run_pending()
        time.sleep(30)

# ─── בוט טלגרם ────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    key  = text.lower().strip()

    await update.message.reply_text(f"🔍 מחפש את '{text}'...")

    # חיפוש במילון המובנה
    ticker = STOCK_NAMES.get(key) or STOCK_NAMES.get(text.upper())
    if not ticker:
        ticker = text.upper()

    # ניתוח
    data = analyze(ticker)
    if not data and not ticker.endswith(".TA"):
        data = analyze(ticker + ".TA")
        if data:
            ticker = ticker + ".TA"

    if not data:
        await update.message.reply_text(
            f"❌ לא מצאתי את '{text}'\n\n"
            f"נסה: NVDA, TEVA, AAPL\n"
            f"או: nvidia, tesla, apple\n"
            f"או: נווידיה, טבע, אפל"
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
    cap_str = f"{cap/1_000_000_000:.1f}B" if cap >= 1_000_000_000 else \
              f"{cap/1_000_000:.0f}M"      if cap >= 1_000_000      else "—"

    if score >= 80:   rec = "קנייה חזקה ✅✅"
    elif score >= 65: rec = "כניסה ✅"
    elif score >= 50: rec = "שמור על הגדר ⚠️"
    else:             rec = "אל תיכנס ❌"

    maya_line = f"\n📢 המאיה: {', '.join(maya)}" if maya else ""
    name      = ticker.replace(".TA","")

    msg = (
        f"📊 {name}\n\n"
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

# ─── הרצה ראשית ───────────────────────────────────────
if __name__ == "__main__":
    print("✅ מערכת סורק מניות מופעלת!")
    t1 = threading.Thread(target=run_scheduler, daemon=True)
    t1.start()
    t2 = threading.Thread(target=run_tracker, daemon=True)
    t2.start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ בוט טלגרם פעיל!")
    app.run_polling(drop_pending_updates=True)