import re
from dataclasses import dataclass, field

PATTERNS = {
    "emergency": [
        r"\bsuicid\w*", r"\bkill (?:my|him|her|me)self\b", r"\bend my life\b", r"\bkhud ?kushi\b", r"आत्महत्या", r"मर जा(?:ऊं|ना|ऊँ)",
        r"\b(?:beat|beating|hit|hitting|attack\w*|assault\w*)\b.{0,40}\b(?:me|us|my)\b", r"\bthreat\w* to (?:kill|beat|harm)\b",
        r"\bjaan se maar", r"जान से मार", r"\bmaar(?:a|te|ta|pit)\b", r"मार(?:ा|ते|पीट)", r"\bdhamki\b", r"धमकी",
        r"\blocked (?:me|us) (?:in|inside)\b",
    ],
    "criminal": [
        r"\barrest\w*", r"\bfir\b", r"\bpolice\b", r"\bbail\b", r"\bjail\b", r"\bwarrant\b", r"\bchargesheet\b", r"\bgiraftar\w*",
        r"गिरफ्तार", r"पुलिस", r"\bcriminal (?:case|proceedings|complaint)\b", r"\bthana\b", r"थाना", r"\bipc\b", r"\bbns\b", r"\b420\b",
    ],
    "family": [
        r"\bdivorce\b", r"\btalaq\b", r"तलाक", r"\bcustody\b", r"\bdowry\b", r"\bdahej\b", r"दहेज", r"\bdomestic violence\b",
        r"घरेलू हिंसा", r"\balimony\b", r"\bmaintenance from (?:my )?(?:husband|wife)\b",
    ],
    "property_title": [
        r"\bland dispute\b", r"\bproperty (?:title|partition|inheritance)\b", r"\b(?:father|mother|grandfather|grandmother)'?s? will\b", r"\bwill deed\b",
        r"\bzameen\b", r"ज़मीन|जमीन", r"\bbatwara\b", r"\bancestral\b",
    ],
    "eviction": [
        r"\bevict\w*", r"\bvacate\b.{0,40}\b(?:days?|notice|suit)\b", r"बेदखल", r"\bkhali kar(?:o|na|ne)\b.{0,30}\b(?:notice|din)\b",
    ],
    "court_date": [
        r"\bsummons\b", r"\bcourt (?:date|hearing|case against me)\b", r"\bnext date\b", r"समन", r"\bpeshi\b", r"पेशी",
    ],
}

COMPILED = {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in PATTERNS.items()}

REASONS = {
    "emergency": "your safety may be at risk",
    "criminal": "this involves police or a criminal matter",
    "family": "this is a family law matter",
    "property_title": "this is a property ownership or inheritance dispute",
    "eviction": "you are being threatened with eviction, which has strict legal steps",
    "court_date": "there may be a court date, which you must not miss",
}


@dataclass
class ScreenResult:
    flags: list[str] = field(default_factory=list)
    matches: dict = field(default_factory=dict)

    @property
    def emergency(self) -> bool:
        return "emergency" in self.flags

    @property
    def out_of_scope(self) -> bool:
        return any(f in self.flags for f in ("criminal", "family", "property_title"))

    @property
    def needs_lawyer(self) -> bool:
        return bool(self.flags)

    def reasons(self) -> list[str]:
        return [REASONS[f] for f in self.flags]


def screen(text: str) -> ScreenResult:
    result = ScreenResult()
    for flag, patterns in COMPILED.items():
        hits = [m.group(0) for p in patterns if (m := p.search(text))]
        if hits:
            result.flags.append(flag)
            result.matches[flag] = hits
    return result


EMERGENCY_REPLY = (
    "Your safety comes first.\n"
    "- If you are in danger right now, call 112 (police / ambulance).\n"
    "- Women can call 181 (women helpline).\n"
    "- If you are thinking of harming yourself, please call Tele-MANAS on 14416. It is free and available all the time.\n"
    "- For a free government lawyer, call NALSA on 15100.\n\n"
    "आपकी सुरक्षा सबसे ज़रूरी है। खतरा हो तो अभी 112 पर कॉल करें। महिलाएँ 181 पर कॉल कर सकती हैं। "
    "अगर आप खुद को नुकसान पहुँचाने की सोच रहे हैं तो 14416 (Tele-MANAS) पर बात करें। मुफ़्त वकील के लिए 15100 पर कॉल करें।\n\n"
    "When you are safe, I can still help you with the money or paperwork side of your problem."
)
