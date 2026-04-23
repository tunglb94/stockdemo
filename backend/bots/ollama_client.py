"""
Gọi Ollama API local để lấy quyết định trading từ LLM.
"""
import json
import logging
import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
TIMEOUT = 120  # Qwen 30B cần thời gian suy nghĩ


def ask_llm(model: str, system_prompt: str, user_message: str) -> dict | None:
    """
    Gửi market context tới Ollama, nhận quyết định trading dạng JSON.
    Trả về dict hoặc None nếu lỗi.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt + _json_instruction()},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "options": {"temperature": 0.3},  # Ít random hơn cho trading
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        return _parse_json(content)
    except requests.exceptions.ConnectionError:
        logger.error("Ollama không chạy. Hãy chạy: ollama serve")
        return None
    except Exception as e:
        logger.error(f"Lỗi gọi Ollama ({model}): {e}")
        return None


def _json_instruction() -> str:
    return """

QUAN TRỌNG: Trả lời CHỈ bằng JSON hợp lệ, không giải thích thêm. Format:
{
  "analysis": "nhận xét ngắn về thị trường hôm nay",
  "decisions": [
    {
      "symbol": "VCB",
      "action": "BUY",
      "quantity": 100,
      "reason": "lý do ngắn"
    }
  ],
  "hold": ["HPG", "FPT"],
  "sell_all": []
}
action chỉ được là: "BUY", "SELL", "HOLD"
quantity phải là bội số của 100 (lô tối thiểu sàn VN)
Nếu không muốn giao dịch hôm nay, trả về decisions rỗng: []
"""


def _parse_json(content: str) -> dict | None:
    """Tìm và parse JSON từ response LLM (có thể có text thừa xung quanh)."""
    content = content.strip()

    # Thử parse thẳng
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Tìm block JSON trong markdown ```json ... ```
    import re
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Tìm { ... } đầu tiên
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    logger.warning(f"Không parse được JSON từ LLM: {content[:200]}")
    return None
