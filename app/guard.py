import re
from dataclasses import dataclass, field

from app.knowledge import provisions_by_id

TAG = re.compile(r"\[\[([^\[\]\n]{1,60})\]\]")
DASHES = dict.fromkeys(map(ord, "\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d"), "-")
SINGLE_TAG = re.compile(r"(?<!\[)\[([A-Za-z]{2,}[0-9]*\s*[-\u2010-\u2015\u2212\ufe63\uff0d][^\[\]\n]{1,30})\](?!\])")
SECTION_MENTION = re.compile(
    r"\b(?:sections?|secs?\.|s\.|articles?|art\.|rules?)\s*([0-9]+[A-Z]?(?:\([0-9a-z]+\))*)"
    r"|\border\s+([IVXL]{2,})\b"
    r"|धारा\s*([0-9]+[A-Z]?)",
    re.IGNORECASE,
)
ACT_HINTS = [
    (re.compile(r"consumer protection \(consumer disputes", re.I), "CPRULES2020"),
    (re.compile(r"e-?commerce", re.I), "ECOM2020"),
    (re.compile(r"consumer protection|\bCPA\b", re.I), "CPA2019"),
    (re.compile(r"code on wages|wage code", re.I), "COW2019"),
    (re.compile(r"negotiable|\bNI Act\b", re.I), "NI1881"),
    (re.compile(r"contract act", re.I), "ICA1872"),
    (re.compile(r"limitation act", re.I), "LIM1963"),
    (re.compile(r"civil procedure|\bCPC\b", re.I), "CPC"),
    (re.compile(r"legal services", re.I), "LSA1987"),
    (re.compile(r"tenancy", re.I), "MTA2021"),
]
CASE_LAW = [
    re.compile(r"\bAIR\s+(?:19|20)\d{2}\b"),
    re.compile(r"\(\s*(?:19|20)\d{2}\s*\)\s*\d+\s*SCC\b"),
    re.compile(r"\b\d+\s*SCC\s*\d+"),
    re.compile(r"\bSCR\b"),
    re.compile(r"\b[A-Z][A-Za-z.&]+(?:\s+[A-Z][A-Za-z.&]+){0,5}\s+(?:v\.|vs\.?|versus)\s+(?:State|Union|[A-Z][A-Za-z.&]+)"),
    re.compile(r"\b(?:Supreme Court|High Court|SC|HC|NCDRC)\b[^.\n]{0,40}\b(?:held|ruled|observed|decided)\b", re.IGNORECASE),
    re.compile(r"\b(?:in the case of|landmark judgment|precedent)\b", re.IGNORECASE),
]
OUTDATED = {
    r"\bIndian Penal Code\b|\bIPC\b": "CRIM-2024",
    r"\bCode of Criminal Procedure\b|\bCrPC\b|\bCr\.P\.C\b": "CRIM-2024",
    r"\bPayment of Wages Act\b|\bMinimum Wages Act\b": "COW2019-S69",
    r"\bConsumer Protection Act,?\s*1986\b": "CPA2019-S35",
    r"\be-?Daakhil\b": "CPA2019-S35",
}
OUTDATED_RE = {re.compile(k, re.IGNORECASE): v for k, v in OUTDATED.items()}
DRAFT_BLOCK = re.compile(r"=== DRAFT START ===(.*?)=== DRAFT END ===", re.DOTALL)


@dataclass
class GuardReport:
    valid_tags: list[str] = field(default_factory=list)
    invalid_tags: list[str] = field(default_factory=list)
    unverified_mentions: list[str] = field(default_factory=list)
    case_law: list[str] = field(default_factory=list)
    outdated: list[str] = field(default_factory=list)

    @property
    def violations(self) -> int:
        return len(self.invalid_tags) + len(self.unverified_mentions) + len(self.case_law)

    def feedback(self) -> str:
        notes = []
        if self.invalid_tags:
            notes.append(f"You cited ids that are not in the SOURCES list: {', '.join(self.invalid_tags)}. Remove them.")
        if self.unverified_mentions:
            notes.append(f"You mentioned legal references that are not in SOURCES: {', '.join(self.unverified_mentions)}. Remove them or cite a SOURCES id instead.")
        if self.case_law:
            notes.append("You referred to court judgments or case citations. Never cite cases. Remove them.")
        return " ".join(notes)

    def as_dict(self) -> dict:
        return {
            "valid_tags": self.valid_tags,
            "invalid_tags": self.invalid_tags,
            "unverified_mentions": self.unverified_mentions,
            "case_law": self.case_law,
            "outdated": self.outdated,
            "violations": self.violations,
        }


def _clean_id(raw: str) -> str:
    return re.sub(r"\s+", "", raw.translate(DASHES)).upper()


def normalize_tags(text: str) -> str:
    known = provisions_by_id()
    out = TAG.sub(lambda m: f"[[{_clean_id(m.group(1))}]]", text)

    def single(match):
        pid = _clean_id(match.group(1))
        return f"[[{pid}]]" if pid in known else match.group(0)

    return SINGLE_TAG.sub(single, out)


def _prefix(pid: str) -> str:
    return pid.split("-")[0]


def _allowed_pairs(allowed_ids: list[str]) -> set[tuple[str, str]]:
    corpus = provisions_by_id()
    pairs = set()
    for pid in allowed_ids:
        for n in corpus[pid]["numbers"]:
            pairs.add((_prefix(pid), n.lower()))
            pairs.add((_prefix(pid), n.split("(")[0].lower()))
    return pairs


def _mention_ok(number: str, window: str, pairs: set[tuple[str, str]]) -> bool:
    base = number.split("(")[0]
    for pattern, prefix in ACT_HINTS:
        if pattern.search(window):
            return (prefix, number) in pairs or (prefix, base) in pairs
    return any(n in (number, base) for _, n in pairs)


ABBREV = re.compile(r"\b(v|vs|Rs|No|Sec|Secs|s|Art|Ltd|Pvt|Dr|Mr|Mrs|Ms|St|Co|Corp|Inc|etc|i\.e|e\.g)\.", re.IGNORECASE)


def _split(line: str) -> list[str]:
    protected = ABBREV.sub(lambda m: m.group(0).replace(".", "\u2024"), line)
    return [p.replace("\u2024", ".") for p in re.split(r"(?<=[.!?।])\s+", protected)]


def _sentences(text: str) -> list[str]:
    out = []
    for line in text.split("\n"):
        out.extend(_split(line))
    return out


def check(text: str, allowed_ids: list[str]) -> GuardReport:
    report = GuardReport()
    allowed = set(allowed_ids)
    for tag in TAG.findall(text):
        target = report.valid_tags if tag in allowed else report.invalid_tags
        if tag not in target:
            target.append(tag)
    pairs = _allowed_pairs(allowed_ids)
    scrubbed = TAG.sub("", text)
    scrubbed = re.sub(r"\[FILL:[^\]]*\]", "", scrubbed)
    for m in SECTION_MENTION.finditer(scrubbed):
        number = (m.group(1) or m.group(2) or m.group(3) or "").lower()
        window = scrubbed[m.end() : m.end() + 90]
        if number and not _mention_ok(number, window, pairs):
            if m.group(0).strip() not in report.unverified_mentions:
                report.unverified_mentions.append(m.group(0).strip())
    for sentence in _sentences(scrubbed):
        if any(p.search(sentence) for p in CASE_LAW):
            report.case_law.append(sentence.strip()[:160])
    for pattern, replacement in OUTDATED_RE.items():
        hit = pattern.search(scrubbed)
        if hit and replacement not in report.outdated:
            report.outdated.append(replacement)
    return report


def enforce(text: str, allowed_ids: list[str], report: GuardReport) -> str:
    out = text
    for tag in report.invalid_tags:
        out = out.replace(f"[[{tag}]]", "")
    for mention in report.unverified_mentions:
        out = re.sub(re.escape(mention) + r"(?![0-9A-Za-z(])", "[reference removed: not in verified sources]", out)
    if report.case_law:
        kept = []
        for line in out.split("\n"):
            pieces = [p for p in _split(line) if not any(c.search(p) for c in CASE_LAW)]
            kept.append(" ".join(pieces))
        out = "\n".join(kept)
    return re.sub(r"[ \t]{2,}", " ", out).strip()


def render_citations(text: str, allowed_ids: list[str]) -> tuple[str, list[dict]]:
    corpus = provisions_by_id()
    order: list[str] = []

    def number(match):
        pid = match.group(1)
        if pid not in allowed_ids:
            return ""
        if pid not in order:
            order.append(pid)
        return f"[{order.index(pid) + 1}]"

    rendered = TAG.sub(number, text)
    citations = []
    for i, pid in enumerate(order, start=1):
        p = corpus[pid]
        citations.append(
            {
                "n": i,
                "id": pid,
                "kind": p["kind"],
                "label": "Practical guidance" if p["kind"] == "practice" else f"{p['act']}, {p['ref']}",
                "title": p["title"],
                "source": p["source"],
            }
        )
    return rendered, citations


def render_inline(text: str, allowed_ids: list[str]) -> str:
    corpus = provisions_by_id()

    def label(match):
        pid = match.group(1)
        if pid not in allowed_ids or corpus[pid]["kind"] == "practice":
            return ""
        p = corpus[pid]
        return f"({p['ref']}, {p['act']})"

    out = re.sub(r"[ \t]{2,}", " ", TAG.sub(label, text))
    return re.sub(r"[ \t]+([.,;:])", r"\1", out)


def outdated_notes(report: GuardReport) -> list[str]:
    corpus = provisions_by_id()
    return [corpus[pid]["summary"] for pid in report.outdated]


def split_draft(text: str) -> tuple[str, str | None]:
    m = DRAFT_BLOCK.search(text)
    if not m:
        return text, None
    draft = m.group(1).strip()
    body = (text[: m.start()] + "\n(See the draft below.)\n" + text[m.end() :]).strip()
    return body, draft
