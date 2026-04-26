"""
Auto-analyzer cho Futures positions.
Sau mỗi round trading, quét tất cả lệnh đã đóng chưa được phân tích,
gọi Qwen → lưu FuturesTradeAnalysis + LearnedLesson (nếu đủ điều kiện).
"""
import json
import logging

logger = logging.getLogger(__name__)

ANALYZER_MODEL = "qwen2.5:7b"
FALLBACK_MODEL = "phi4:14b"

SYSTEM_PROMPT = """Bạn là chuyên gia phân tích giao dịch futures crypto với 10 năm kinh nghiệm.
Phân tích lệnh trade, đánh giá chất lượng quyết định, và rút ra bài học thực tế.
Trả về JSON hợp lệ, viết "why" bằng tiếng Việt ngắn gọn (2-3 câu).
- verdict: "Quyết định tốt" | "Có thể tốt hơn" | "Quyết định sai"
- quality_score: 0.0–1.0
- lesson: bài học cụ thể hoặc null nếu trade bình thường
- lesson_tags: mảng từ [universal, momentum, contrarian, scalper, timing, macro, altcoin]
- lesson_polarity: "GOOD" (nên làm) hoặc "WARNING" (nên tránh)"""


def _build_prompt(pos) -> str:
    pnl = float(pos.realized_pnl or 0)
    entry = float(pos.entry_price)
    exit_p = float(pos.exit_price or entry)
    margin = float(pos.margin_usd)
    notional = margin * pos.leverage
    pnl_pct = (pnl / margin * 100) if margin else 0
    verdict = "WIN" if pnl > 0 else ("LOSS" if pnl < 0 else "BREAKEVEN")
    if pos.status == "LIQUIDATED":
        verdict = "LIQUIDATED"

    return f"""Phân tích lệnh futures:
- Bot: {pos.user.username} | Mã: {pos.asset.symbol} | Hướng: {pos.direction}
- Entry: ${entry:.4f} → Exit: ${exit_p:.4f}
- Margin: ${margin:.0f} × {pos.leverage}x | Notional: ${notional:.0f}
- PnL: ${pnl:+.2f} ({pnl_pct:+.1f}% trên margin) | Trạng thái: {verdict}
- Mở: {pos.opened_at} | Đóng: {pos.closed_at}

Trả về JSON:
{{"why": "...", "verdict": "{verdict}", "quality_score": 0.0, "lesson": null, "lesson_tags": ["universal"], "lesson_polarity": "GOOD"}}"""


def analyze_one(pos) -> bool:
    """Phân tích 1 position, lưu cache + lesson. Trả True nếu thành công."""
    from bots.ollama_client import ask_llm
    from crypto.models import FuturesTradeAnalysis, LearnedLesson

    prompt = _build_prompt(pos)
    pnl = float(pos.realized_pnl or 0)
    margin = float(pos.margin_usd)
    pnl_pct = (pnl / margin * 100) if margin else 0

    data = ask_llm(ANALYZER_MODEL, SYSTEM_PROMPT, prompt,
                   num_ctx=2048, num_predict=350, temperature=0.2)
    if not data:
        data = ask_llm(FALLBACK_MODEL, SYSTEM_PROMPT, prompt,
                       num_ctx=2048, num_predict=350, temperature=0.2)
    if not data:
        logger.warning(f"[auto-analyzer] LLM không phản hồi cho position {pos.id}")
        return False

    quality = float(data.get("quality_score") or 0.5)
    quality = max(0.0, min(1.0, quality))
    data["quality_score"] = quality

    # Lưu cache
    try:
        FuturesTradeAnalysis.objects.create(
            position=pos,
            analysis_text=json.dumps(data, ensure_ascii=False),
            quality_score=quality,
        )
    except Exception as e:
        logger.warning(f"[auto-analyzer] Không lưu được cache pos {pos.id}: {e}")
        return False

    # Lưu lesson nếu đủ điều kiện
    lesson_text = data.get("lesson")
    if lesson_text and abs(pnl_pct) > 5.0 and quality >= 0.55:
        try:
            tags = data.get("lesson_tags", ["universal"])
            tags_str = ",".join(str(t).strip() for t in tags) if isinstance(tags, list) else str(tags)
            polarity = data.get("lesson_polarity", "")
            if polarity not in ("GOOD", "WARNING"):
                polarity = "WARNING" if pnl < 0 else "GOOD"
            LearnedLesson.objects.create(
                source_order=None,
                source_bot=pos.user.username,
                lesson_text=lesson_text,
                polarity=polarity,
                tags=tags_str,
                quality_score=quality,
                pnl_at_extraction=pnl_pct,
            )
            logger.info(f"[auto-analyzer] Lesson saved từ pos {pos.id} ({pos.asset.symbol} {pos.direction} {pnl_pct:+.1f}%): {lesson_text[:80]}")
        except Exception as e:
            logger.warning(f"[auto-analyzer] Không lưu được lesson: {e}")

    return True


def run_auto_analysis(max_per_run: int = 5):
    """
    Quét tất cả closed positions chưa có analysis.
    Xử lý tối đa max_per_run mỗi lần gọi để không block bot loop.
    Ưu tiên positions có |PnL| lớn nhất trước.
    """
    from crypto.models import FuturesPosition

    # Lấy các positions chưa có analysis — ưu tiên |PnL| lớn nhất
    from crypto.models import FuturesTradeAnalysis
    analyzed_ids = set(FuturesTradeAnalysis.objects.values_list("position_id", flat=True))
    unanalyzed = list(
        FuturesPosition.objects
        .filter(status__in=["CLOSED", "LIQUIDATED"])
        .exclude(id__in=analyzed_ids)
        .select_related("user", "asset")
        .extra(select={"abs_pnl": "ABS(COALESCE(realized_pnl, 0))"})
        .order_by("-abs_pnl")[:max_per_run]
    )
    count = len(unanalyzed)
    if count == 0:
        return

    logger.info(f"[auto-analyzer] Bắt đầu phân tích {count} lệnh chưa được xử lý...")
    done = 0
    for pos in unanalyzed:
        try:
            if analyze_one(pos):
                done += 1
        except Exception as e:
            logger.error(f"[auto-analyzer] Lỗi pos {pos.id}: {e}")

    logger.info(f"[auto-analyzer] Hoàn thành {done}/{count} lệnh.")
