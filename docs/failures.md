# Failures and Lessons

Each entry: what we tried, what broke, why, and what we learned.

## Hindi words broke in a normal regex

- **What we tried:** removed punctuation with a regex using `\W`.
- **What broke:** "मेरा ऑर्डर कब आएगा" became "म र ऑर डर कब आएग". Hindi vowel signs are Unicode marks, not letters, so the regex treated them as separators.
- **Fix:** keep characters by Unicode category (letters, marks, numbers) with `unicodedata`.
- **Lesson:** always test text handling with real Hindi text, not only English.
