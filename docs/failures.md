# Failures and Lessons

Each entry: what we tried, what broke, why, and what we learned.

## Hindi words broke in a normal regex

- **What we tried:** removed punctuation with a regex using `\W`.
- **What broke:** "मेरा ऑर्डर कब आएगा" became "म र ऑर डर कब आएग". Hindi vowel signs are Unicode marks, not letters, so the regex treated them as separators.
- **Fix:** keep characters by Unicode category (letters, marks, numbers) with `unicodedata`.
- **Lesson:** always test text handling with real Hindi text, not only English.

## Whisper wrote Hinglish in Devanagari, so WER showed 100%

- **What we tried:** Whisper small (faster-whisper, CPU, int8, language auto) on our 5 real clips.
- **What happened:** Corpus WER was 100%. Every word counted as wrong, even though the model understood much of the speech.
- **Why:** Our correct text is in Roman letters, and Whisper wrote everything in Devanagari, including English words (for example "order" came out as "अडर"). A word in another script never matches, so no word matched.
- **What this teaches:** Raw WER is not a fair number for Hinglish until both texts are in the same script. We will add script handling, and Character Error Rate next to WER.
- **Other things seen (5 clips, one speaker, so only a first look):** numbers and English words were often misheard, the fast WhatsApp clip was worst and also took about 16 seconds instead of about 3, and the 4-second pause in one clip did not confuse the model.

## Forcing English made Whisper translate instead of transcribe

- **What we tried:** the same 5 clips with the language set to English.
- **What happened:** Whisper wrote English sentences with the same meaning (for example "When will my order arrive?") instead of the words that were spoken. WER dropped to 91.4%, but this is not better listening. The words are different, so they still count as wrong.
- **Why it matters:** WER punishes a correct meaning written in different words. A voice agent needs the meaning (the request, the numbers, the names) more than the exact words. We need a second check: did the agent understand the request?
- **Seen in this run:** in English mode the number "do zero paanch saat" came out right as 2057, and "bees se ekkis" as "20 to 21". In both modes the word "failed" was heard as "fill", which changes what the customer asked for.
- **Limits:** only 5 clips from one speaker, so this is a first look, not a conclusion.

## Whisper wrote Hinglish in Devanagari, so WER showed 100%

- **What we tried:** Whisper small (faster-whisper, CPU, int8, language auto) on our 5 real clips.
- **What happened:** Corpus WER was 100%. Every word counted as wrong, even though the model understood much of the speech.
- **Why:** Our correct text is in Roman letters, and Whisper wrote everything in Devanagari, including English words (for example "order" came out as "अडर"). A word in another script never matches, so no word matched.
- **What this teaches:** Raw WER is not a fair number for Hinglish until both texts are in the same script. We will add script handling, and Character Error Rate next to WER.
- **Other things seen (5 clips, one speaker, so only a first look):** numbers and English words were often misheard, the fast WhatsApp clip was worst and also took about 16 seconds instead of about 3, and the 4-second pause in one clip did not confuse the model.
