"""
Ollama API client for trading bots.
"""
import json
import logging
import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"

# Per-model HTTP timeout (seconds)
TIMEOUT_BY_MODEL = {
    "phi4:14b":               120,
    "qwen2.5:14b":            120,
    "deepseek-coder-v2:16b":  120,
    "deepseek-v2:16b":        120,
    "qwen3.5:9b":              90,
    # legacy
    "gemma3:12b":             120,
    "mistral-nemo:12b":       120,
    "hermes3":                120,
    "qwen3:8b":                90,
}
TIMEOUT_DEFAULT = 150

# num_ctx defaults — only used when caller doesn't override
# Futures bots pass num_ctx=4096 explicitly (context ~2000 tokens, no need for 16k)
NUM_CTX_DEFAULT = {
    "phi4:14b":              16384,   # VN stock bots use long prompts
    "qwen2.5:14b":           16384,
    "deepseek-coder-v2:16b": 16384,
    "deepseek-v2:16b":       16384,
    "qwen3.5:9b":            16384,
    # legacy
    "gemma3:12b":            16384,
    "mistral-nemo:12b":      16384,
    "hermes3":               16384,
    "qwen3:8b":              16384,
}

# Models that don't support Ollama's native format:"json" mode
_NO_JSON_FORMAT: set = set()


def ask_llm(
    model: str,
    system_prompt: str,
    user_message: str,
    append_json_instruction: bool = True,
    num_ctx: int | None = None,
    num_predict: int | None = None,
    temperature: float = 0.3,
    keep_alive: str = "10m",
) -> dict | None:
    """
    Call Ollama and get a trading decision as JSON.

    Args:
        num_ctx:      KV-cache size. Override per caller — futures bots use 4096,
                      VN-stock bots keep default (16384).
        num_predict:  Max output tokens. Futures JSON response ≈ 300–400 tokens.
        keep_alive:   Keep model in VRAM after call. "10m" = 10 minutes.
                      Avoids reload cost when same model runs multiple bots back-to-back.
    """
    resolved_ctx     = num_ctx     if num_ctx     is not None else NUM_CTX_DEFAULT.get(model, 16384)
    resolved_predict = num_predict if num_predict is not None else (500 if "30b" in model else 1200)

    sys_content = system_prompt + (_json_instruction() if append_json_instruction else "")
    payload = {
        "model":      model,
        "keep_alive": keep_alive,
        "messages": [
            {"role": "system", "content": sys_content},
            {"role": "user",   "content": user_message},
        ],
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": resolved_predict,
            "num_ctx":     resolved_ctx,
        },
    }
    if model not in _NO_JSON_FORMAT:
        payload["format"] = "json"

    try:
        timeout = TIMEOUT_BY_MODEL.get(model, TIMEOUT_DEFAULT)
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        content = resp.json()["message"]["content"]
        return _parse_json(content)
    except requests.exceptions.ConnectionError:
        logger.error("Ollama not running. Start with: ollama serve")
        return None
    except Exception as e:
        logger.error(f"Ollama error ({model}): {e}")
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
    """Extract and parse JSON from LLM response (may have surrounding text)."""
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    import re
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    logger.warning(f"Cannot parse JSON from LLM: {content[:200]}")
    return None
