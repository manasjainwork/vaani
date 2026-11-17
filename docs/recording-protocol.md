# Recording protocol

This page explains how we collect the first 50 real Hinglish clips, and how we keep it safe and fair.

## Why we do this first

When a voice bot sounds dumb, the cause is often simpler than the language model. The speech model may have heard a wrong word, or the system may have cut off the speaker too early. So we score speech recognition (ASR) and voice activity detection (VAD) on real clips before we touch the language model.

## The plan

- **50 clips**, each 5 to 15 seconds long.
- **At least 5 different speakers** if possible, with different voices and accents.
- Mix of conditions:
    - 20 clean clips in a quiet room
    - 10 with background noise (fan, street, low TV)
    - 10 fast, casual speech
    - 10 with a long pause in the middle (this tests whether the system cuts the speaker off)
- Content: everyday voice-agent talk in natural Hinglish, like order status, refund, booking and complaints. Include English words, Hindi words, numbers and dates mixed together.

## Consent and privacy (non-negotiable)

- Every speaker agrees first. A simple written message is enough: "I agree that my voice clips can be used for this research project. I know the audio stays private on the owner's laptop, and only anonymous scores are published."
- Speakers are anonymous in the data (`s1`, `s2`, ...). No real names.
- No real phone numbers, addresses or personal details in what people say. Use made-up ones.
- Audio never goes into git or the public repo. If a speaker asks, we delete their clips.

## How to record and prepare

Record with any phone voice recorder app. Then convert each file to 16 kHz mono WAV:

```bash
ffmpeg -i input.m4a -ar 16000 -ac 1 clip_001.wav
```

## How to label

- **Reference text:** type exactly what was said, in lowercase Roman Hinglish, with simple and consistent spelling. Speech models often write Hindi words in Devanagari, so the scoring step will need to handle script differences. That is planned work, not solved yet.
- **Turn times:** mark when the person starts and stops speaking, in seconds. A free tool like Audacity (labels) works. These times are the truth we compare the VAD against.

## The manifest file

One line of JSON per clip. See `data_example/manifest.example.jsonl` for the format. The loader in `src/vaani/data.py` refuses a clip that has no consent, an empty transcript, or broken turn times.

## What "turns" means in the manifest

Each clip holds exactly **one user turn**: one thing the speaker wanted to say, from the first word to the last word.

The `turns` list holds the stretches of real speech inside that one turn. A gap between two stretches is a **pause inside the turn**, not the end of the turn. This matters for the VAD test:

- If the system decides the turn is over while the speaker is still going to continue (inside a gap, or before the last stretch ends), that is a **cut-off**.
- If the system waits much longer than needed after the last stretch ends, that is a **late end**.
- If the system hears speech where there is only noise, that is a **false start**.

Turn times are marked by a human listening to the clip. A script may suggest them, but the suggestion is never the truth.
