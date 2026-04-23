"""
Price feed cho crypto (CoinGecko) và commodity (Yahoo Finance).
Chạy mỗi 60 giây trong background thread.
"""
import threading
import time
import logging
import requests
from decimal import Decimal

logger = logging.getLogger(__name__)

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"

CRYPTO_ASSETS = [
    {"symbol": "BTC",  "name": "Bitcoin",           "coingecko_id": "bitcoin",             "rank": 1},
    {"symbol": "ETH",  "name": "Ethereum",           "coingecko_id": "ethereum",            "rank": 2},
    {"symbol": "BNB",  "name": "BNB",                "coingecko_id": "binancecoin",         "rank": 3},
    {"symbol": "SOL",  "name": "Solana",             "coingecko_id": "solana",              "rank": 4},
    {"symbol": "XRP",  "name": "XRP",                "coingecko_id": "ripple",              "rank": 5},
    {"symbol": "DOGE", "name": "Dogecoin",           "coingecko_id": "dogecoin",            "rank": 6},
    {"symbol": "ADA",  "name": "Cardano",            "coingecko_id": "cardano",             "rank": 7},
    {"symbol": "AVAX", "name": "Avalanche",          "coingecko_id": "avalanche-2",         "rank": 8},
    {"symbol": "SHIB", "name": "Shiba Inu",          "coingecko_id": "shiba-inu",           "rank": 9},
    {"symbol": "TRX",  "name": "TRON",               "coingecko_id": "tron",                "rank": 10},
    {"symbol": "TON",  "name": "Toncoin",            "coingecko_id": "the-open-network",    "rank": 11},
    {"symbol": "LINK", "name": "Chainlink",          "coingecko_id": "chainlink",           "rank": 12},
    {"symbol": "DOT",  "name": "Polkadot",           "coingecko_id": "polkadot",            "rank": 13},
    {"symbol": "POL",  "name": "Polygon (POL)",       "coingecko_id": "polygon-ecosystem-token", "rank": 14},
    {"symbol": "LTC",  "name": "Litecoin",           "coingecko_id": "litecoin",            "rank": 15},
    {"symbol": "UNI",  "name": "Uniswap",            "coingecko_id": "uniswap",             "rank": 16},
    {"symbol": "APT",  "name": "Aptos",              "coingecko_id": "aptos",               "rank": 17},
    {"symbol": "ATOM", "name": "Cosmos",             "coingecko_id": "cosmos",              "rank": 18},
    {"symbol": "XLM",  "name": "Stellar",            "coingecko_id": "stellar",             "rank": 19},
    {"symbol": "NEAR", "name": "NEAR Protocol",      "coingecko_id": "near",                "rank": 20},
    {"symbol": "OP",   "name": "Optimism",           "coingecko_id": "optimism",            "rank": 21},
    {"symbol": "INJ",  "name": "Injective",          "coingecko_id": "injective-protocol",  "rank": 22},
    {"symbol": "ARB",  "name": "Arbitrum",           "coingecko_id": "arbitrum",            "rank": 23},
    {"symbol": "MKR",  "name": "Maker",              "coingecko_id": "maker",               "rank": 24},
    {"symbol": "RUNE", "name": "THORChain",          "coingecko_id": "thorchain",           "rank": 25},
    {"symbol": "FIL",  "name": "Filecoin",           "coingecko_id": "filecoin",            "rank": 26},
    {"symbol": "VET",  "name": "VeChain",            "coingecko_id": "vechain",             "rank": 27},
    {"symbol": "SUI",  "name": "Sui",                "coingecko_id": "sui",                 "rank": 28},
    {"symbol": "ICP",  "name": "Internet Computer",  "coingecko_id": "internet-computer",   "rank": 29},
    {"symbol": "ALGO", "name": "Algorand",           "coingecko_id": "algorand",            "rank": 30},
    # --- Batch 2: thêm 30 mã mới ---
    {"symbol": "BCH",   "name": "Bitcoin Cash",      "coingecko_id": "bitcoin-cash",                "rank": 31},
    {"symbol": "XMR",   "name": "Monero",            "coingecko_id": "monero",                      "rank": 32},
    {"symbol": "HBAR",  "name": "Hedera",            "coingecko_id": "hedera-hashgraph",            "rank": 33},
    {"symbol": "AAVE",  "name": "Aave",              "coingecko_id": "aave",                        "rank": 34},
    {"symbol": "KAS",   "name": "Kaspa",             "coingecko_id": "kaspa",                       "rank": 35},
    {"symbol": "PEPE",  "name": "Pepe",              "coingecko_id": "pepe",                        "rank": 36},
    {"symbol": "WIF",   "name": "dogwifhat",         "coingecko_id": "dogwifcoin",                  "rank": 37},
    {"symbol": "RENDER","name": "Render",            "coingecko_id": "render-token",                "rank": 38},
    {"symbol": "STX",   "name": "Stacks",            "coingecko_id": "blockstack",                  "rank": 39},
    {"symbol": "FTM",   "name": "Fantom",            "coingecko_id": "fantom",                      "rank": 40},
    {"symbol": "SEI",   "name": "Sei",               "coingecko_id": "sei-network",                 "rank": 41},
    {"symbol": "TIA",   "name": "Celestia",          "coingecko_id": "celestia",                    "rank": 42},
    {"symbol": "JUP",   "name": "Jupiter",           "coingecko_id": "jupiter-exchange-solana",     "rank": 43},
    {"symbol": "BONK",  "name": "Bonk",              "coingecko_id": "bonk",                        "rank": 44},
    {"symbol": "GRT",   "name": "The Graph",         "coingecko_id": "the-graph",                   "rank": 45},
    {"symbol": "EGLD",  "name": "MultiversX",        "coingecko_id": "elrond-erd-2",                "rank": 46},
    {"symbol": "FLOW",  "name": "Flow",              "coingecko_id": "flow",                        "rank": 47},
    {"symbol": "MANA",  "name": "Decentraland",      "coingecko_id": "decentraland",                "rank": 48},
    {"symbol": "SAND",  "name": "The Sandbox",       "coingecko_id": "the-sandbox",                 "rank": 49},
    {"symbol": "AXS",   "name": "Axie Infinity",     "coingecko_id": "axie-infinity",               "rank": 50},
    {"symbol": "CRV",   "name": "Curve DAO",         "coingecko_id": "curve-dao-token",             "rank": 51},
    {"symbol": "COMP",  "name": "Compound",          "coingecko_id": "compound-governance-token",   "rank": 52},
    {"symbol": "SNX",   "name": "Synthetix",         "coingecko_id": "havven",                      "rank": 53},
    {"symbol": "EOS",   "name": "EOS",               "coingecko_id": "eos",                         "rank": 54},
    {"symbol": "DASH",  "name": "Dash",              "coingecko_id": "dash",                        "rank": 55},
    {"symbol": "ZEC",   "name": "Zcash",             "coingecko_id": "zcash",                       "rank": 56},
    {"symbol": "FLOKI", "name": "Floki",             "coingecko_id": "floki",                       "rank": 57},
    {"symbol": "NOT",   "name": "Notcoin",           "coingecko_id": "notcoin",                     "rank": 58},
    {"symbol": "STRK",  "name": "Starknet",          "coingecko_id": "starknet",                    "rank": 59},
    {"symbol": "PYTH",  "name": "Pyth Network",      "coingecko_id": "pyth-network",                "rank": 60},
]

COMMODITY_ASSETS = [
    {"symbol": "XAU",    "name": "Gold (oz)",           "yfinance_ticker": "GC=F",  "rank": 61},
    {"symbol": "WTI",    "name": "Crude Oil (bbl)",     "yfinance_ticker": "CL=F",  "rank": 62},
    {"symbol": "XAG",    "name": "Silver (oz)",         "yfinance_ticker": "SI=F",  "rank": 63},
    {"symbol": "COPPER", "name": "Copper (lb)",         "yfinance_ticker": "HG=F",  "rank": 64},
    {"symbol": "NATGAS", "name": "Natural Gas (MMBtu)", "yfinance_ticker": "NG=F",  "rank": 65},
    {"symbol": "XPT",    "name": "Platinum (oz)",       "yfinance_ticker": "PL=F",  "rank": 66},
    {"symbol": "WHEAT",  "name": "Wheat (bu)",          "yfinance_ticker": "ZW=F",  "rank": 67},
    {"symbol": "CORN",   "name": "Corn (bu)",           "yfinance_ticker": "ZC=F",  "rank": 68},
    {"symbol": "COFFEE", "name": "Coffee (lb)",         "yfinance_ticker": "KC=F",  "rank": 69},
    {"symbol": "SUGAR",  "name": "Sugar (lb)",          "yfinance_ticker": "SB=F",  "rank": 70},
    {"symbol": "COTTON", "name": "Cotton (lb)",         "yfinance_ticker": "CT=F",  "rank": 71},
    {"symbol": "BRENT",  "name": "Brent Crude (bbl)",   "yfinance_ticker": "BZ=F",  "rank": 72},
]

_feed_started = False
_feed_lock = threading.Lock()


def ensure_assets():
    from crypto.models import CryptoAsset
    for a in CRYPTO_ASSETS:
        CryptoAsset.objects.get_or_create(
            symbol=a["symbol"],
            defaults={"name": a["name"], "category": "CRYPTO",
                      "coingecko_id": a["coingecko_id"], "rank": a["rank"]},
        )
    for a in COMMODITY_ASSETS:
        CryptoAsset.objects.get_or_create(
            symbol=a["symbol"],
            defaults={"name": a["name"], "category": "COMMODITY",
                      "yfinance_ticker": a["yfinance_ticker"], "rank": a["rank"]},
        )


def _fetch_coingecko() -> list:
    ids = ",".join(a["coingecko_id"] for a in CRYPTO_ASSETS)
    resp = requests.get(
        COINGECKO_URL,
        params={
            "vs_currency": "usd",
            "ids": ids,
            "order": "market_cap_desc",
            "per_page": 100,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h",
        },
        timeout=25,
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    return resp.json()


def _fetch_yahoo(ticker: str) -> float | None:
    try:
        resp = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
            params={"interval": "1m", "range": "1d"},
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible)"},
        )
        meta = resp.json()["chart"]["result"][0]["meta"]
        return float(meta.get("regularMarketPrice") or meta.get("previousClose") or 0)
    except Exception:
        return None


def _save_crypto(data: list):
    from crypto.models import CryptoAsset, CryptoSnapshot

    id_map = {a["coingecko_id"]: a["symbol"] for a in CRYPTO_ASSETS}
    assets = {a.symbol: a for a in CryptoAsset.objects.filter(category="CRYPTO")}

    snaps = []
    for item in data:
        symbol = id_map.get(item.get("id", ""))
        asset = assets.get(symbol)
        if not asset:
            continue
        price = item.get("current_price")
        if not price:
            continue
        snaps.append(CryptoSnapshot(
            asset=asset,
            price_usd=Decimal(str(price)),
            change_24h=item.get("price_change_percentage_24h") or 0,
            volume_24h=Decimal(str(item.get("total_volume") or 0)),
            market_cap=Decimal(str(item.get("market_cap") or 0)),
        ))
    if snaps:
        CryptoSnapshot.objects.bulk_create(snaps)
    return len(snaps)


def _save_commodity(symbol: str, price: float, change_24h: float = 0):
    from crypto.models import CryptoAsset, CryptoSnapshot
    try:
        asset = CryptoAsset.objects.get(symbol=symbol)
        CryptoSnapshot.objects.create(
            asset=asset,
            price_usd=Decimal(str(round(price, 4))),
            change_24h=round(change_24h, 4),
        )
    except Exception as e:
        logger.error(f"Commodity save {symbol}: {e}")


def _feed_loop():
    time.sleep(15)
    try:
        ensure_assets()
        logger.info("Crypto: assets ensured.")
    except Exception as e:
        logger.error(f"Crypto ensure_assets: {e}")

    prev = {}  # symbol -> price (for computing change)

    while True:
        # --- Crypto via CoinGecko ---
        try:
            data = _fetch_coingecko()
            n = _save_crypto(data)
            logger.info(f"Crypto: {n} prices saved from CoinGecko.")
        except Exception as e:
            logger.error(f"CoinGecko fetch error: {e}")

        # --- Commodities via Yahoo Finance ---
        for sym, ticker in [("XAU", "GC=F"), ("WTI", "CL=F")]:
            try:
                price = _fetch_yahoo(ticker)
                if price:
                    old = prev.get(sym)
                    change = ((price - old) / old * 100) if old else 0
                    _save_commodity(sym, price, change)
                    prev[sym] = price
            except Exception as e:
                logger.error(f"Yahoo {sym}: {e}")

        time.sleep(60)


def start_crypto_feed():
    global _feed_started
    with _feed_lock:
        if _feed_started:
            return
        _feed_started = True
    t = threading.Thread(target=_feed_loop, daemon=True, name="crypto_feed")
    t.start()
    logger.info("Crypto price feed thread started.")
