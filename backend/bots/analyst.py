"""
Hermes3 AI Analyst — đọc kết quả 5 bot, đánh giá chiến lược, lưu DB.
Chạy sau mỗi vòng run_bots hoàn thành.
"""
import json
import logging
import re
import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
ANALYST_MODEL = "hermes3"

_SYSTEM_PROMPT = """Bạn là chuyên gia phân tích chứng khoán AI, nhiệm vụ đánh giá khách quan 5 AI trading bot trên sàn VN.

Trả lời CHỈ bằng JSON hợp lệ, không giải thích thêm:
{
  "market_outlook": "BULLISH" | "BEARISH" | "NEUTRAL",
  "summary": "nhận xét tổng quan 2-3 câu: thị trường hôm nay thế nào, bot nào đang thắng, xu hướng chung",
  "evaluations": [
    {
      "bot": "tên display_name của bot",
      "verdict": "WINNING" | "LOSING" | "NEUTRAL",
      "score": <số nguyên 1-10>,
      "comment": "1-2 câu nhận xét chiến lược: điểm mạnh, điểm yếu, rủi ro"
    }
  ],
  "best_strategy": "bot nào đang làm tốt nhất và tại sao (1 câu)",
  "warning": "cảnh báo rủi ro quan trọng nhất hoặc null nếu không có"
}"""


def _build_prompt(bot_results: list) -> str:
    lines = ["=== KẾT QUẢ GIAO DỊCH 5 AI BOT ===\n"]
    for r in bot_results:
        total = r.get("total_value", 100_000_000)
        cash = r.get("cash", 0)
        pnl_pct = r.get("pnl_pct", 0)
        decisions = r.get("decisions_this_round", [])
        holdings = r.get("holdings", [])

        lines.append(f"[{r['display_name']}] model={r['model']}")
        lines.append(f"  Chien luoc: {r.get('strategy_short', '')}")
        lines.append(f"  P&L: {pnl_pct:+.2f}% | Tong tai san: {total:,.0f}d")
        lines.append(f"  Tien mat: {cash:,.0f}d ({cash/total*100:.1f}% danh muc)")
        lines.append(f"  Dang giu: {len(holdings)} ma co phieu")

        if decisions:
            lines.append(f"  Lenh dat vong nay ({len(decisions)}):")
            for d in decisions[:5]:
                lines.append(f"    {d.get('action','?')} {d.get('quantity',0)} {d.get('symbol','?')}: {d.get('reason','')}")
        else:
            lines.append("  Khong dat lenh vong nay (HOLD)")
        lines.append("")

    return "\n".join(lines)


def _parse_json(content: str) -> dict | None:
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def run_analyst(bot_results: list) -> bool:
    """
    Gọi Hermes3 phân tích kết quả các bot, lưu vào DB.
    bot_results: list of dict với keys: display_name, model, strategy_short,
                 total_value, cash, pnl_pct, holdings, decisions_this_round
    Trả về True nếu thành công.
    """
    if not bot_results:
        return False

    prompt = _build_prompt(bot_results)
    payload = {
        "model": ANALYST_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": 0.2},
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
        if resp.status_code == 404:
            logger.warning(f"[analyst] Model {ANALYST_MODEL} chua duoc tai. Chay: ollama pull {ANALYST_MODEL}")
            return False
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        result = _parse_json(content)
    except requests.exceptions.ConnectionError:
        logger.error("[analyst] Ollama khong chay.")
        return False
    except Exception as e:
        logger.error(f"[analyst] Loi goi Hermes: {e}")
        return False

    if not result:
        logger.warning("[analyst] Khong parse duoc JSON tu Hermes.")
        return False

    try:
        from bots.models import BotAnalysis
        BotAnalysis.objects.create(
            market_outlook=result.get("market_outlook", "NEUTRAL"),
            summary=result.get("summary", ""),
            evaluations=result.get("evaluations", []),
            best_strategy=result.get("best_strategy", ""),
            warning=result.get("warning"),
        )
        logger.info(f"[analyst] Da luu phan tich: {result.get('market_outlook')} — {result.get('summary','')[:60]}")
        return True
    except Exception as e:
        logger.error(f"[analyst] Loi luu DB: {e}")
        return False
