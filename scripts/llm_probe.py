"""Find out why the model's answers sometimes come back empty.

The same five customer sentences are sent three ways:
  chat_default : /api/chat as it is
  chat_no_think: /api/chat with "think": false
  raw_chatml   : /api/generate with the chat format written by hand

Example:
    uv run python scripts/llm_probe.py
"""

from __future__ import annotations

import json
import urllib.request

from agent_demo import DEFAULT_LLM, SYSTEM_PROMPT

CHAT_URL = "http://localhost:11434/api/chat"
GENERATE_URL = "http://localhost:11434/api/generate"
HEARD = [
    "बाई मेरे अडर कब आयगा मैंने कल सुबही किया ता",
    "मेरा रिफवन का स्तेटस क्या है अडर नमवर दो जीरो पाज साथ फाज",
    "मुजे कल शाम चार भजे का अपोईन्में बुक करना है और रिमाइंटर भी लगा देना",
    "यार पेमिंट होगेट था, पर आप मे प्ल थिखार है. इक बच्छ कर दो प्लीज्",
    "रिलिवरी आट्रेस चेंज करना है, प्लैत नमबर भीस ले एक्किस कर दो.",
]
REPEATS = 2
OPTIONS = {"temperature": 0.2, "num_predict": 120}


def post_json(url: str, body: dict) -> dict:
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.load(response)


def ask(mode: str, heard: str) -> tuple[str, int, int]:
    """Returns the answer text, how many characters went to 'thinking', and the token count."""
    if mode == "raw_chatml":
        prompt = (
            f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
            f"<|im_start|>user\n{heard}<|im_end|>\n<|im_start|>assistant\n"
        )
        options = {**OPTIONS, "stop": ["<|im_end|>"]}
        data = post_json(
            GENERATE_URL,
            {"model": DEFAULT_LLM, "prompt": prompt, "raw": True, "stream": False, "options": options},
        )
        return data.get("response", "").strip(), 0, data.get("eval_count") or 0
    body = {
        "model": DEFAULT_LLM,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": heard},
        ],
        "stream": False,
        "options": OPTIONS,
    }
    if mode == "chat_no_think":
        body["think"] = False
    data = post_json(CHAT_URL, body)
    message = data.get("message", {})
    return (
        message.get("content", "").strip(),
        len(message.get("thinking") or ""),
        data.get("eval_count") or 0,
    )


def main() -> None:
    print(f"model: {DEFAULT_LLM}\n")
    for mode in ("chat_default", "chat_no_think", "raw_chatml"):
        empty = total = tokens = thinking = 0
        sample = ""
        for heard in HEARD:
            for _ in range(REPEATS):
                text, thinking_chars, token_count = ask(mode, heard)
                total += 1
                tokens += token_count
                thinking += thinking_chars
                if not text:
                    empty += 1
                elif not sample:
                    sample = text
        print(f"{mode:14} empty {empty}/{total}, average tokens {tokens / total:.0f}, "
              f"average thinking characters {thinking / total:.0f}")
        if sample:
            print(f"    example answer: {sample[:90]}")


if __name__ == "__main__":
    main()
