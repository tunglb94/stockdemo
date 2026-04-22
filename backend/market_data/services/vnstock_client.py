"""
Wrapper lấy dữ liệu chứng khoán VN qua vnstock (v3.5+).
Dùng VCIQuote trực tiếp để tránh lỗi Company init.
Dữ liệu trả về đơn vị: VNĐ (đã nhân 1000 từ giá gốc nghìn đồng).
"""
import logging
from decimal import Decimal
from typing import Optional
from datetime import date, timedelta

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


def fetch_current_price(symbol: str) -> Optional[dict]:
    """
    Lấy giá hiện tại của một mã.
    Dùng dữ liệu daily history — hoạt động 24/7 không phụ thuộc giờ giao dịch.
    """
    end = date.today().strftime("%Y-%m-%d")
    start = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
    df = _get_history_df(symbol, start, end, "1D")

    if df is None:
        return None

    try:
        # Giá trong vnstock đơn vị nghìn đồng → nhân 1000
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else latest

        current = float(latest["close"]) * 1000
        ref = float(prev["close"]) * 1000          # Giá tham chiếu = close hôm qua
        ceiling = round(ref * 1.07, 0)             # Trần HOSE +7%
        floor_p = round(ref * 0.93, 0)             # Sàn HOSE -7%
        change = current - ref
        change_pct = (change / ref * 100) if ref else 0

        return {
            "symbol": symbol,
            "current_price": Decimal(str(int(current))),
            "reference_price": Decimal(str(int(ref))),
            "ceiling_price": Decimal(str(int(ceiling))),
            "floor_price": Decimal(str(int(floor_p))),
            "open_price": Decimal(str(int(float(latest["open"]) * 1000))),
            "high_price": Decimal(str(int(float(latest["high"]) * 1000))),
            "low_price": Decimal(str(int(float(latest["low"]) * 1000))),
            "volume": int(latest["volume"]),
            "change": Decimal(str(round(change, 0))),
            "change_percent": Decimal(str(round(change_pct, 4))),
            "value": Decimal(str(int(float(latest["volume"]) * current))),
            "bid_price_1": None, "bid_vol_1": None,
            "bid_price_2": None, "bid_vol_2": None,
            "bid_price_3": None, "bid_vol_3": None,
            "ask_price_1": None, "ask_vol_1": None,
            "ask_price_2": None, "ask_vol_2": None,
            "ask_price_3": None, "ask_vol_3": None,
        }
    except Exception as e:
        logger.error(f"Lỗi xử lý giá {symbol}: {e}")
        return None


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
    """
    Lấy giá tất cả 30 mã VN30.
    Delay 4s giữa mỗi mã để tránh rate limit (free tier: 20 req/phút).
    """
    import time
    results = []
    for i, symbol in enumerate(VN30_SYMBOLS):
        if i > 0:
            time.sleep(4)  # 4s × 30 mã = 2 phút, an toàn với 20 req/phút
        data = fetch_current_price(symbol)
        if data:
            results.append(data)
            logger.info(f"OK {symbol}: {data['current_price']}")
        else:
            logger.warning(f"Bỏ qua {symbol}")
    return results
