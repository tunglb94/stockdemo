"""
Qwen 3.5 trade analyzer.
Nhận một CryptoOrder → phân tích WHY bot trade, đánh giá chất lượng, rút ra lesson.
"""
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

ANALYZER_MODEL = "qwen3.5:9b"

ANALYZER_SYSTEM = """Bạn là chuyên gia phân tích giao dịch crypto với 10 năm kinh nghiệm.
Nhiệm vụ: phân tích một lệnh trade cụ thể của AI bot, giải thích tại sao bot quyết định như vậy, đánh giá chất lượng quyết định, và rút ra bài học nếu có.

Trả về JSON với format chính xác sau:
{
  "why": "Giải thích chi tiết (3-5 câu) vì sao bot quyết định trade này dựa trên thông tin và reasoning lúc đó",
  "verdict": "Quyết định tốt",
  "quality_score": 0.75,
  "lesson": "Bài học cụ thể (1-2 câu) đáng ghi nhớ cho các bot khác, hoặc null nếu trade bình thường",
  "lesson_tags": ["universal"],
  "lesson_polarity": "GOOD"
}

Quy tắc:
- verdict: chỉ dùng 1 trong 3 giá trị: "Quyết định tốt" | "Có thể tốt hơn" | "Quyết định sai"
- quality_score: 0.0 (sai hoàn toàn) đến 1.0 (hoàn hảo) — đánh giá dựa trên timing, logic reasoning, và outcome
- lesson: null nếu trade không có gì đặc biệt để học. Chỉ ghi khi có insight rõ ràng.
- lesson_tags: mảng gồm 1+ tag từ danh sách: universal, momentum, contrarian, scalper, value, commodity, altcoin, macro, timing
- lesson_polarity: "GOOD" (bài học tích cực, nên làm) hoặc "WARNING" (bài học tiêu cực, nên tránh)
- PnL = 0% là HÒA (break even), không phải thua
- Viết "why" bằng tiếng Việt, rõ ràng và thực tế"""


def _get_bot_def(username: str) -> dict | None:
    from crypto.bots.definitions import CRYPTO_BOTS
    for b in CRYPTO_BOTS:
        if b["username"] == username:
            return b
    return None


def _get_username_from_user(user) -> str | None:
    from crypto.bots.definitions import CRYPTO_BOTS
    for b in CRYPTO_BOTS:
        if b["email"] == user.email:
            return b["username"]
    return None


def _get_post_trade_price(asset) -> float | None:
    try:
        snap = asset.snapshots.latest("timestamp")
        return float(snap.price_usd)
    except Exception:
        return None


def _get_round_context(bot_username: str, before_dt) -> str:
    from crypto.models import BotRoundLog
    log = (
        BotRoundLog.objects
        .filter(bot_username=bot_username, created_at__lte=before_dt)
        .order_by("-created_at")
        .first()
    )
    if log and log.analysis_text:
        return log.analysis_text[:600]
    return "(Không có dữ liệu bối cảnh thị trường lúc đó)"


def build_analyze_prompt(order, bot_username: str, bot_def: dict) -> str:
    strategy_summary = bot_def["system_prompt"]
    # Lấy phần sau "===" đầu tiên để tóm gọn chiến lược
    lines = strategy_summary.split("\n")
    strategy_lines = [l for l in lines if l.strip() and not l.startswith("===")]
    strategy_short = " ".join(strategy_lines[:8])[:400]

    current_price = _get_post_trade_price(order.asset)
    round_context = _get_round_context(bot_username, order.created_at)

    lines = [
        "=== THÔNG TIN BOT ===",
        f"Tên: {bot_def['display_name']}",
        f"Model: {bot_def['model']}",
        f"Chiến lược: {strategy_short}",
        "",
        "=== CHI TIẾT LỆNH ===",
        f"Loại lệnh: {order.side} {order.asset.symbol}",
        f"Số lượng: {float(order.quantity):.6f} {order.asset.symbol}",
        f"Giá khớp: ${float(order.price_usd):.4f}",
        f"Tổng giá trị: ${float(order.total_usd):.2f}",
        f"Thời gian: {order.created_at.strftime('%d/%m/%Y %H:%M:%S')}",
    ]

    if order.side == "SELL" and order.cost_basis_usd:
        pnl_pct = float((order.price_usd - order.cost_basis_usd) / order.cost_basis_usd * 100)
        pnl_usd = float(order.pnl_usd) if order.pnl_usd else 0

        if abs(pnl_pct) < 0.01:
            ket_qua = "HÒA (break even)"
        elif pnl_pct > 0:
            ket_qua = f"THẮNG +{pnl_pct:.2f}%"
        else:
            ket_qua = f"THUA {pnl_pct:.2f}%"

        lines += [
            f"Giá vốn trung bình: ${float(order.cost_basis_usd):.4f}",
            f"Realized PnL: ${pnl_usd:+.2f} ({pnl_pct:+.2f}%)",
            f"Kết quả: {ket_qua}",
        ]
    elif order.side == "BUY" and current_price:
        buy_price = float(order.price_usd)
        unreal_pct = (current_price - buy_price) / buy_price * 100
        direction = f"+{unreal_pct:.2f}% (đang lời)" if unreal_pct > 0.01 else (
            f"{unreal_pct:.2f}% (đang lỗ)" if unreal_pct < -0.01 else "~0% (hòa)"
        )
        lines += [
            f"Giá hiện tại: ${current_price:.4f}",
            f"Unrealized PnL hiện tại: {direction}",
        ]

    lines += [
        "",
        "=== LÝ DO BOT ĐƯA RA LÚC ĐÓ ===",
        order.bot_reasoning if order.bot_reasoning else "(Lệnh cũ, chưa có reasoning được lưu)",
        "",
        "=== BỐI CẢNH THỊ TRƯỜNG LÚC ĐÓ ===",
        round_context,
        "",
        "=== YÊU CẦU ===",
        f"Hãy phân tích lệnh {order.side} {order.asset.symbol} này theo format JSON đã quy định.",
    ]

    return "\n".join(lines)


def analyze_trade(order) -> dict | None:
    """
    Gọi Qwen 3.5 để phân tích 1 lệnh trade.
    Trả về dict với: why, verdict, quality_score, lesson, lesson_tags, lesson_polarity
    """
    from bots.ollama_client import ask_llm

    bot_username = _get_username_from_user(order.user)
    if not bot_username:
        logger.warning(f"Cannot find bot def for user {order.user.email}")
        return None

    bot_def = _get_bot_def(bot_username)
    if not bot_def:
        return None

    prompt = build_analyze_prompt(order, bot_username, bot_def)

    result = ask_llm(
        model=ANALYZER_MODEL,
        system_prompt=ANALYZER_SYSTEM,
        user_message=prompt,
        append_json_instruction=False,
        num_predict=900,
        temperature=0.2,  # thấp hơn để phân tích chính xác, ít hallucinate
    )

    if not result:
        logger.error(f"Qwen analyzer returned None for order {order.id}")
        return None

    # Validate và normalize output
    result.setdefault("why", "Không có phân tích.")
    result.setdefault("verdict", "Có thể tốt hơn")
    result.setdefault("quality_score", 0.5)
    result.setdefault("lesson", None)
    result.setdefault("lesson_tags", ["universal"])
    result.setdefault("lesson_polarity", "GOOD")

    # Clamp quality_score về 0.0–1.0
    try:
        result["quality_score"] = max(0.0, min(1.0, float(result["quality_score"])))
    except (ValueError, TypeError):
        result["quality_score"] = 0.5

    return result


def should_extract_lesson(order, analysis: dict) -> bool:
    """Chỉ extract lesson từ SELL với |PnL| > 5% và quality_score đủ cao."""
    if order.side != "SELL":
        return False
    if not order.cost_basis_usd or not order.pnl_usd:
        return False
    if not analysis.get("lesson"):
        return False

    pnl_pct = float((order.price_usd - order.cost_basis_usd) / order.cost_basis_usd * 100)
    quality = analysis.get("quality_score", 0)

    return abs(pnl_pct) > 5.0 and quality >= 0.55


def save_learned_lesson(order, bot_username: str, analysis: dict):
    from crypto.models import LearnedLesson

    pnl_pct = None
    if order.cost_basis_usd and order.cost_basis_usd > 0:
        pnl_pct = float((order.price_usd - order.cost_basis_usd) / order.cost_basis_usd * 100)

    tags = analysis.get("lesson_tags", ["universal"])
    if isinstance(tags, list):
        tags_str = ",".join(str(t).strip() for t in tags)
    else:
        tags_str = str(tags)

    polarity = analysis.get("lesson_polarity", "GOOD")
    if polarity not in ("GOOD", "WARNING"):
        polarity = "WARNING" if (pnl_pct or 0) < 0 else "GOOD"

    LearnedLesson.objects.create(
        source_order=order,
        source_bot=bot_username,
        lesson_text=analysis["lesson"],
        polarity=polarity,
        tags=tags_str,
        quality_score=analysis.get("quality_score", 0.5),
        pnl_at_extraction=pnl_pct,
    )
    logger.info(f"Saved lesson from order {order.id}: {analysis['lesson'][:80]}")
