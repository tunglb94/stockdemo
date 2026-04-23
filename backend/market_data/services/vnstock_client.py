"""
Wrapper lấy dữ liệu chứng khoán VN qua vnstock (v3.5+).
Dùng VCIQuote trực tiếp để tránh lỗi Company init.
Dữ liệu trả về đơn vị: VNĐ (đã nhân 1000 từ giá gốc nghìn đồng).
"""
import logging
import os
from decimal import Decimal
from typing import Optional
from datetime import date, timedelta
from django.conf import settings

# --- NẠP API KEY CHO VNSTOCK ---
# Lấy API Key từ Django settings (nếu có) hoặc trực tiếp từ os.environ (qua file .env)
api_key = getattr(settings, 'VNSTOCK_API_KEY', os.environ.get('VNSTOCK_API_KEY', ''))
if api_key:
    os.environ['VNSTOCK_API_KEY'] = api_key

logger = logging.getLogger(__name__)

VN30_SYMBOLS = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR",
    "HDB", "HPG", "MBB", "MSN", "MWG", "PLX", "POW", "SAB",
    "SHB", "SSB", "SSI", "STB", "TCB", "TPB", "VCB", "VHM",
    "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
]

# Tên công ty VN30 hardcode — tránh gọi API listing hay bị lỗi
VN30_COMPANY_NAMES = {
    "ACB": "Ngân hàng TMCP Á Châu",
    "BCM": "Tổng Công ty Đầu tư và Phát triển Công nghiệp",
    "BID": "Ngân hàng TMCP Đầu tư và Phát triển Việt Nam",
    "BVH": "Tập đoàn Bảo Việt",
    "CTG": "Ngân hàng TMCP Công Thương Việt Nam",
    "FPT": "Công ty Cổ phần FPT",
    "GAS": "Tổng Công ty Khí Việt Nam",
    "GVR": "Tập đoàn Công nghiệp Cao su Việt Nam",
    "HDB": "Ngân hàng TMCP Phát triển TP.HCM",
    "HPG": "Công ty Cổ phần Tập đoàn Hòa Phát",
    "MBB": "Ngân hàng TMCP Quân đội",
    "MSN": "Công ty Cổ phần Tập đoàn Masan",
    "MWG": "Công ty Cổ phần Đầu tư Thế Giới Di Động",
    "PLX": "Tập đoàn Xăng dầu Việt Nam",
    "POW": "Tổng Công ty Điện lực Dầu khí Việt Nam",
    "SAB": "Công ty Cổ phần Bia Rượu Nước giải khát Sài Gòn",
    "SHB": "Ngân hàng TMCP Sài Gòn - Hà Nội",
    "SSB": "Ngân hàng TMCP Đông Nam Á",
    "SSI": "Công ty Cổ phần Chứng khoán SSI",
    "STB": "Ngân hàng TMCP Sài Gòn Thương Tín",
    "TCB": "Ngân hàng TMCP Kỹ thương Việt Nam",
    "TPB": "Ngân hàng TMCP Tiên Phong",
    "VCB": "Ngân hàng TMCP Ngoại thương Việt Nam",
    "VHM": "Công ty Cổ phần Vinhomes",
    "VIB": "Ngân hàng TMCP Quốc tế Việt Nam",
    "VIC": "Tập đoàn Vingroup",
    "VJC": "Công ty Cổ phần Hàng không VietJet",
    "VNM": "Công ty Cổ phần Sữa Việt Nam",
    "VPB": "Ngân hàng TMCP Việt Nam Thịnh Vượng",
    "VRE": "Công ty Cổ phần Vincom Retail",
}


def _get_quote(symbol: str):
    """Lấy Quote object trực tiếp từ VCI, bỏ qua Company init."""
    from vnstock.explorer.vci import Quote as VCIQuote
    return VCIQuote(symbol)


def _get_history_df(symbol: str, start: str, end: str, interval: str = "1D"):
    """Lấy DataFrame lịch sử giá."""
    import io, sys
    # Redirect stdout/stderr tạm thời để tránh lỗi encoding tiếng Việt trên Windows
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        q = _get_quote(symbol)
        df = q.history(start=start, end=end, interval=interval)
        return df if (df is not None and not df.empty) else None
    except Exception as e:
        logger.error(f"Lỗi lấy history {symbol}: {e}")
        return None
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def _is_market_open() -> bool:
    """Kiểm tra giờ giao dịch HOSE (GMT+7): 9:00-11:30 và 13:00-14:45."""
    from datetime import datetime
    import zoneinfo
    now = datetime.now(zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh"))
    if now.weekday() >= 5:  # Thứ 7, CN
        return False
    t = now.time()
    from datetime import time as dtime
    return (dtime(9, 0) <= t <= dtime(11, 30)) or (dtime(13, 0) <= t <= dtime(14, 45))



def fetch_current_price(symbol: str) -> Optional[dict]:
    """
    Lấy giá hiện tại — chỉ 1 API call/mã:
    - Trong giờ giao dịch: intraday() → realtime ~15s delay
    - Ngoài giờ: history daily → giá đóng cửa gần nhất
    """
    if _is_market_open():
        return _fetch_price_intraday(symbol)
    return _fetch_price_daily(symbol)


def _fetch_price_daily(symbol: str) -> Optional[dict]:
    end = date.today().strftime("%Y-%m-%d")
    start = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    df = _get_history_df(symbol, start, end, "1D")
    if df is None:
        return None
    try:
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else latest
        ref = float(prev["close"]) * 1000
        current = float(latest["close"]) * 1000
        volume = int(latest["volume"])
        return _build_price_dict(
            symbol=symbol,
            current=current, ref=ref, volume=volume,
            open_p=float(latest["open"]) * 1000,
            high_p=float(latest["high"]) * 1000,
            low_p=float(latest["low"]) * 1000,
        )
    except Exception as e:
        logger.error(f"Lỗi xử lý giá daily {symbol}: {e}")
        return None


def _fetch_price_intraday(symbol: str) -> Optional[dict]:
    import io, sys
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        q = _get_quote(symbol)
        df = q.intraday(show_log=False)
        if df is None or df.empty:
            return None
        last = df.iloc[-1]
        current = float(last["price"]) * 1000
        volume = int(df["volume"].sum())
        ref = float(df.iloc[0]["price"]) * 1000
        buy_vol = int(df[df["match_type"] == "Buy"]["volume"].sum())
        sell_vol = int(df[df["match_type"] == "Sell"]["volume"].sum())
        result = _build_price_dict(
            symbol=symbol,
            current=current, ref=ref, volume=volume,
            open_p=ref, high_p=float(df["price"].max()) * 1000,
            low_p=float(df["price"].min()) * 1000,
        )
        # Dùng bid/ask slot 1 để hiển thị KL mua/bán tổng ngày
        result["bid_vol_1"] = buy_vol
        result["ask_vol_1"] = sell_vol
        return result
    except Exception as e:
        logger.error(f"Lỗi xử lý giá intraday {symbol}: {e}")
        return None
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def _build_price_dict(symbol, current, ref, volume, open_p, high_p, low_p) -> dict:
    ceiling = round(ref * 1.07, 0)
    floor_p = round(ref * 0.93, 0)
    change = current - ref
    change_pct = (change / ref * 100) if ref else 0
    return {
        "symbol": symbol,
        "current_price": Decimal(str(int(current))),
        "reference_price": Decimal(str(int(ref))),
        "ceiling_price": Decimal(str(int(ceiling))),
        "floor_price": Decimal(str(int(floor_p))),
        "open_price": Decimal(str(int(open_p))),
        "high_price": Decimal(str(int(high_p))),
        "low_price": Decimal(str(int(low_p))),
        "volume": volume,
        "change": Decimal(str(round(change, 0))),
        "change_percent": Decimal(str(round(change_pct, 4))),
        "value": Decimal(str(int(volume * current))),
        "bid_price_1": None, "bid_vol_1": None,
        "bid_price_2": None, "bid_vol_2": None,
        "bid_price_3": None, "bid_vol_3": None,
        "ask_price_1": None, "ask_vol_1": None,
        "ask_price_2": None, "ask_vol_2": None,
        "ask_price_3": None, "ask_vol_3": None,
    }


def fetch_stock_history(symbol: str, start: str, end: str, interval: str = "1D") -> list:
    """Lấy lịch sử giá cho biểu đồ nến (TradingView format)."""
    df = _get_history_df(symbol, start, end, interval)
    if df is None:
        return []

    try:
        results = []
        for _, row in df.iterrows():
            results.append({
                "time": str(row["time"])[:10],
                "open": float(row["open"]) * 1000,
                "high": float(row["high"]) * 1000,
                "low": float(row["low"]) * 1000,
                "close": float(row["close"]) * 1000,
                "volume": int(row["volume"]),
            })
        return results
    except Exception as e:
        logger.error(f"Lỗi format history {symbol}: {e}")
        return []


def fetch_all_vn30_prices() -> list[dict]:
    """Lấy giá 30 mã VN30 (giữ để tương thích)."""
    return _fetch_symbols_batch(VN30_SYMBOLS)


def fetch_all_prices(symbols: Optional[list[str]] = None) -> list[dict]:
    """
    Lấy giá tất cả mã. Nếu không truyền symbols thì lấy từ DB.
    VN30 được fetch trước, sau đó các mã còn lại.
    """
    if symbols is None:
        from market_data.models import Stock
        symbols = list(Stock.objects.filter(is_active=True).values_list("symbol", flat=True))

    # VN30 trước, còn lại sau
    vn30_set = set(VN30_SYMBOLS)
    priority = [s for s in VN30_SYMBOLS if s in symbols]
    rest = [s for s in symbols if s not in vn30_set]
    return _fetch_symbols_batch(priority + rest)


def _fetch_symbols_batch(symbols: list[str]) -> list[dict]:
    """Fetch giá hàng loạt — rate limiting do caller quản lý."""
    import time
    results = []

    for symbol in symbols:
        data = fetch_current_price(symbol)
        time.sleep(0.2)
        if data:
            results.append(data)
            logger.info(f"OK {symbol}: {data['current_price']} ({len(results)}/{len(symbols)})")
        else:
            logger.warning(f"Bỏ qua {symbol}")

    return results

def get_all_market_symbols() -> list:
    """Lấy danh sách toàn bộ mã cổ phiếu trên 3 sàn HOSE, HNX, UPCOM."""
    import io, sys
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        from vnstock.explorer.vci import Listing
        listing = Listing()
        df = listing.all_symbols()

        results = []
        for _, row in df.iterrows():
            ticker = str(row.get('symbol', '')).strip()
            if not ticker or len(ticker) > 5:
                continue
            name = str(row.get('organ_name', ticker)).strip()
            results.append({'ticker': ticker, 'comGroupCode': 'HOSE', 'organName': name})
        return results
    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        logger.error(f"Lỗi lấy danh sách toàn thị trường: {e}")
        return []
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr