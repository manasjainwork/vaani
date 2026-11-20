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

## The brain's answers came back empty (Ollama chat template)

- **What we tried:** Qwen3-4B-Instruct-2507 through Ollama's chat endpoint.
- **What happened:** 3 of 5 replies were empty. In a test of 10 calls each, the default chat mode gave 10 empty answers, and the "think off" switch gave 6 empty answers. The model was writing tokens (about 28 per call), but the text field was empty, or it stopped after one token.
- **Our best explanation:** Ollama treats this model as a "thinking" model. It filed the whole answer under a hidden thinking field, and the "think off" switch added an empty think block that made the model stop early. We saw thinking text in the hidden field, but we did not prove every step.
- **Fix:** write the chat format (ChatML) ourselves and send it in raw mode. That gave 0 empty answers in 10 calls.
- **Lesson:** when a model returns nothing, count the tokens and compare different ways of calling it before blaming the model. Also add a guard, so the agent never speaks an empty or non-Hindi reply.

## Whisper wrote different text on different runs

- **What happened:** the same fast WhatsApp clip gave three different texts on three runs, and took 8.8 s once and 19.1 s another time. Our guess is that Whisper retries with random decoding when it is unsure.
- **What we tried first:** temperature 0, to remove the randomness. The text became fixed, but on the fast clip Whisper fell into a loop and wrote one character again and again.
- **Fix:** keep Whisper's normal retry behaviour and fix the random seed. Two runs of the same clip now give identical text.
- **Limits:** checked on one clip, two runs, one machine.
- **Lesson:** an evaluation must give the same number every time, or it cannot show that something improved.

## The agent found the right order from a garbled number, by luck

- **What happened:** speech recognition heard "दो जीरो पाज साथ फाज" for order 2057. The agent replied with the status of order 2057. The first order in its data happened to be the right one.
- **Why it is a risk:** with another order number, the same mistake could show someone else's order.
- **Lesson and next step:** read the number back and ask the customer to confirm before sharing any details, and test with order 3141 and garbled numbers.
- **Related:** requests outside the agent's job (an appointment, a payment problem, an address change) all got "please give your order number". The agent needs a clear rule for what it cannot do.
