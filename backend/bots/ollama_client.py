"""
Gọi Ollama API local để lấy quyết định trading từ LLM.
"""
import json
import logging
import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
TIMEOUT_BY_MODEL = {
    "gemma3:27b":          300,
    "qwen3:30b-a3b":       360,
    "nemotron-3-nano:30b": 360,
    "gemma3:12b":          240,
    "mistral-nemo:12b":    240,
    "hermes3":             240,
    "phi4:14b":            240,
    "qwen2.5:7b":          120,
}
TIMEOUT = 360

# num_ctx per model — increase for models getting empty responses (context overflow)
NUM_CTX_BY_MODEL = {
    "gemma3:27b":           8192,  # 17GB weights — keep ctx small to fit in 16GB VRAM
    "gemma3:12b":          16384,  # 8GB weights + 3GB KV = ~11GB — safe
    "phi4:14b":            16384,  # 9GB weights + 3GB KV = ~12GB — safe
    "mistral-nemo:12b":    16384,
    "nemotron-3-nano:30b":  8192,  # 24GB — heavy CPU offload, keep ctx minimal
    "qwen3:30b-a3b":        8192,  # 18GB MoE, keep ctx small
}

# Models that don't support Ollama's native format:"json" mode
_NO_JSON_FORMAT = {"nemotron-3-nano:30b"}


def ask_llm(model: str, system_prompt: str, user_message: str, append_json_instruction: bool = True) -> dict | None:
    """
    Gửi market context tới Ollama, nhận quyết định trading dạng JSON.
    Trả về dict hoặc None nếu lỗi.
    append_json_instruction=False cho futures/crypto bots có format riêng trong system_prompt.
    """
    # num_predict: limit output tokens. 30b models are verbose and slow.
    num_predict = 500 if "30b" in model else 1200

    num_ctx = NUM_CTX_BY_MODEL.get(model, 16384)

    sys_content = system_prompt + (_json_instruction() if append_json_instruction else "")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": num_predict,
            "num_ctx": num_ctx,
        },
    }
    if model not in _NO_JSON_FORMAT:
        payload["format"] = "json"  # Ép Ollama trả JSON hợp lệ — fix parse lỗi mọi model

    try:
        timeout = TIMEOUT_BY_MODEL.get(model, TIMEOUT)
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
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

CRITICAL: Reply with ONLY valid JSON, no explanation, no markdown, no Vietnamese keys.
Use EXACTLY this format:
{
  "analysis": "short market comment in Vietnamese",
  "decisions": [
    {"symbol": "VCB", "action": "BUY", "quantity": 100, "reason": "short reason"},
    {"symbol": "HPG", "action": "SELL", "quantity": 200, "reason": "short reason"}
  ],
  "hold": ["FPT"],
  "sell_all": []
}
Rules:
- "action" must be exactly "BUY" or "SELL" (uppercase English)
- "symbol" must be uppercase ticker like "VCB", "HPG"
- "quantity" must be multiple of 100
- If no trades today, use: "decisions": []
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
