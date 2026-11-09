import re

SCRIPTS = [
    ("hi", r"[ऀ-ॿ]"),
    ("bn", r"[ঀ-৿]"),
    ("pa", r"[਀-੿]"),
    ("gu", r"[઀-૿]"),
    ("ta", r"[஀-௿]"),
    ("te", r"[ఀ-౿]"),
    ("kn", r"[ಀ-೿]"),
    ("ml", r"[ഀ-ൿ]"),
]
HINGLISH_WORDS = {
    "hai", "hain", "nahi", "nahin", "mera", "meri", "mere", "mujhe", "kya", "kaise", "paisa", "paise", "wapas", "kar", "raha",
    "rahi", "diya", "liya", "tha", "thi", "aur", "bhi", "abhi", "kuch", "ko", "se", "ka", "ki", "ke", "hoga", "karna", "chahiye",
    "bol", "bola", "mahina", "mahine", "makaan", "malik", "kiraya", "kab", "kyun", "toh", "yaar", "bhai", "ji",
}


def detect(text: str) -> str:
    counts = {code: len(re.findall(pattern, text)) for code, pattern in SCRIPTS}
    code, n = max(counts.items(), key=lambda x: x[1])
    letters = len(re.findall(r"[A-Za-z]", text))
    if n and n >= letters * 0.3:
        if code == "hi" and re.search(r"\b(?:आहे|नाही|माझ)", text):
            return "mr"
        return code
    words = re.findall(r"[a-z]+", text.lower())
    if words and sum(w in HINGLISH_WORDS for w in words) / len(words) >= 0.12:
        return "hinglish"
    return "en"
