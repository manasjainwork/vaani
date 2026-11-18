"""Run Whisper on our clips and report the word error rate.

Example:
    uv run python scripts/run_asr_eval.py --device cpu --compute-type int8
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import date
from pathlib import Path

from vaani.asr_eval import corpus_wer, evaluate
from vaani.data import load_manifest


def nvidia_query(field: str) -> str | None:
    """Ask nvidia-smi for one value (for example the GPU name). None if unavailable."""
    try:
        out = subprocess.run(
            ["nvidia-smi", f"--query-gpu={field}", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return out.strip().splitlines()[0]
    except (OSError, subprocess.CalledProcessError, IndexError):
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="data/own50/manifest.jsonl")
    parser.add_argument("--model", default="small")
    parser.add_argument("--language", default="auto", help="auto, hi or en")
    parser.add_argument("--device", default="cpu", help="cpu or cuda")
    parser.add_argument("--compute-type", default="int8")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    clips = load_manifest(args.manifest)
    from faster_whisper import WhisperModel  # imported late, it is a heavy library

    started = time.perf_counter()
    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    load_seconds = time.perf_counter() - started
    memory_mb = nvidia_query("memory.used") if args.device == "cuda" else None
    language = None if args.language == "auto" else args.language

    seconds: dict[str, float] = {}

    def transcribe(path: Path) -> str:
        begin = time.perf_counter()
        segments, _info = model.transcribe(str(path), language=language, beam_size=5)
        text = " ".join(segment.text.strip() for segment in segments)
        seconds[path.stem] = time.perf_counter() - begin
        return text

    scores = evaluate(clips, transcribe)
    overall = corpus_wer(scores)

    print(f"\nmodel={args.model} language={args.language} device={args.device} "
          f"compute_type={args.compute_type}")
    for score in scores:
        r = score.result
        print(f"\n{score.clip_id}: WER {r.wer:.0%} "
              f"(S{r.substitutions} D{r.deletions} I{r.insertions} of {r.reference_words} words, "
              f"{seconds[score.clip_id]:.1f}s)")
        print(f"  said : {score.reference}")
        print(f"  heard: {score.hypothesis}")
    print(f"\nCorpus WER: {overall:.1%}")
    print(f"Model load time: {load_seconds:.1f}s")
    if memory_mb is not None:
        print(f"GPU memory in use after loading the model: {memory_mb} MiB")

    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"asr_{args.model}_{args.language}_{args.device}.json"
    report = {
        "date": date.today().isoformat(),
        "settings": {
            "model": args.model,
            "language": args.language,
            "device": args.device,
            "compute_type": args.compute_type,
        },
        "gpu": nvidia_query("name"),
        "gpu_memory_used_mib_after_load": memory_mb,
        "model_load_seconds": round(load_seconds, 2),
        "corpus_wer": round(overall, 4),
        "clips": [
            {
                "id": s.clip_id,
                "wer": round(s.result.wer, 4),
                "substitutions": s.result.substitutions,
                "deletions": s.result.deletions,
                "insertions": s.result.insertions,
                "reference_words": s.result.reference_words,
                "seconds": round(seconds[s.clip_id], 2),
            }
            for s in scores
        ],
    }
    out_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Saved numbers (no text) to {out_file}")


if __name__ == "__main__":
    main()
