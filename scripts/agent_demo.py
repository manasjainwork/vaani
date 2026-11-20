"""First talking agent: audio file in, spoken reply out (batch, not real time).

Pipeline: Whisper (ears) -> Qwen3 through Ollama (brain) -> Kokoro (mouth).

Example:
    uv run python scripts/agent_demo.py data/own50/audio/clip_001.wav
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf
from say import SAMPLE_RATE, speak

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_LLM = "hf.co/bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF:Q4_K_M"
FALLBACK_REPLY = "माफ़ कीजिए, मैं ठीक से समझ नहीं पाया। क्या आप दोबारा बोल सकते हैं?"

# --8<-- [start:prompt]
SYSTEM_PROMPT = """You are a customer support agent for an online shop, speaking on a phone call.
Reply in Hindi, written in Devanagari, in at most two short sentences.
Use only the order data below. Never invent delivery times or any other facts.
If the customer did not give an order number, ask for it.
If the order number is not in the data, say you cannot find it and offer to connect
the customer to a human agent.
The customer's words come from speech recognition and may contain wrong words.

Order data (this is fake data for testing):
- Order 2057: shipped, will arrive tomorrow evening.
- Order 3141: being packed, will ship the day after tomorrow.
"""
# --8<-- [end:prompt]


def post_json(body: dict) -> dict:
    request = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.load(response)


# --8<-- [start:ask]
def ask_llm(user_text: str, model: str, temperature: float = 0.2) -> tuple[str, dict]:
    """Ask the model. Returns the answer and a few facts about how it was produced.

    We write the chat format (ChatML, the format Qwen was trained on) ourselves and
    send it in "raw" mode. Ollama's own chat template hid this model's answers in a
    "thinking" field, or made it stop after one token.
    """
    prompt = (
        f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{user_text}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )
    data = post_json(
        {
            "model": model,
            "prompt": prompt,
            "raw": True,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": 120, "stop": ["<|im_end|>"]},
        }
    )
    info = {"stop": data.get("done_reason"), "tokens": data.get("eval_count")}
    return data.get("response", "").strip(), info
# --8<-- [end:ask]


# --8<-- [start:guard]
def is_mostly_devanagari(text: str) -> bool:
    """A cheap check that the reply is Hindi and not English (or empty)."""
    devanagari = sum(1 for ch in text if "\u0900" <= ch <= "\u097f")
    latin = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    return devanagari > latin
# --8<-- [end:guard]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", nargs="+", help="one or more 16 kHz mono WAV files")
    parser.add_argument("--llm", default=DEFAULT_LLM)
    parser.add_argument("--whisper", default="small")
    parser.add_argument("--voice", default="hf_beta")
    parser.add_argument("--out-dir", default="data/agent_out")
    args = parser.parse_args()

    import ctranslate2
    from faster_whisper import WhisperModel  # heavy libraries are imported late
    from kokoro import KPipeline

    ctranslate2.set_random_seed(0)  # same clip, same text on every run

    ears = WhisperModel(args.whisper, device="cpu", compute_type="int8")
    mouth = KPipeline(lang_code="h", device="cpu")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for audio_path in args.audio:
        path = Path(audio_path)
        t0 = time.perf_counter()
        segments, _ = ears.transcribe(str(path), language="hi", beam_size=5)
        heard = " ".join(segment.text.strip() for segment in segments)
        t1 = time.perf_counter()
        reply, info = ask_llm(heard, args.llm)
        first_info, retry_info = info, None
        if not reply:  # an empty answer: try once more, a little more freely
            reply, retry_info = ask_llm(heard, args.llm, temperature=0.6)
        t2 = time.perf_counter()
        note = ""
        if not is_mostly_devanagari(reply):
            note = f"  WARNING: the reply was not Hindi, so the fallback line is spoken.\n  raw   : {reply[:200]}"
            reply = FALLBACK_REPLY
        audio = speak(mouth, reply, args.voice, 1.0)
        t3 = time.perf_counter()
        out_path = out_dir / f"{path.stem}_reply.wav"
        sf.write(out_path, np.asarray(audio), SAMPLE_RATE)

        print(f"\n{path.name}")
        print(f"  heard : {heard}")
        print(f"  reply : {reply}")
        print(f"  llm   : first try {first_info}")
        if retry_info is not None:
            print(f"  retry : the first answer was empty, second try {retry_info}")
        if note:
            print(note)
        print(f"  time  : ears {t1 - t0:.1f}s, brain {t2 - t1:.1f}s, mouth {t3 - t2:.1f}s, "
              f"total {t3 - t0:.1f}s")
        print(f"  saved : {out_path} ({len(audio) / SAMPLE_RATE:.1f}s of audio)")


if __name__ == "__main__":
    main()
