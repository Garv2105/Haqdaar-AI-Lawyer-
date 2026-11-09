import json
import re
from functools import lru_cache

from rank_bm25 import BM25Okapi

from app.config import BASE_DIR

TOPICS = ("deposit", "consumer", "salary", "notice")


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9ऀ-ॿ]+", text.lower())


@lru_cache
def load_corpus() -> dict:
    with open(BASE_DIR / "data" / "provisions.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def provisions_by_id() -> dict:
    return {p["id"]: p for p in load_corpus()["provisions"]}


def resources_for(topic: str) -> list[dict]:
    return [r for r in load_corpus()["resources"] if topic in r["topics"]]


def coverage() -> dict:
    corpus = load_corpus()
    by_topic: dict[str, list[str]] = {}
    for p in corpus["provisions"]:
        by_topic.setdefault(p["topic"], []).append(f"{p['act']} - {p['ref']}")
    return {"verified_on": corpus["verified_on"], "topics": by_topic}


def retrieve(topic: str, query: str, k: int = 8) -> list[dict]:
    pool = [p for p in load_corpus()["provisions"] if p["topic"] in (topic, "general")]
    if not pool:
        return []
    docs = [_tokens(" ".join([p["title"], p["summary"], p["keywords"], p["act"]])) for p in pool]
    bm25 = BM25Okapi(docs)
    scores = bm25.get_scores(_tokens(query or topic))
    ranked = sorted(zip(pool, scores), key=lambda x: (x[0]["topic"] != topic, -x[1]))
    topic_items = [p for p, _ in ranked if p["topic"] == topic]
    general_items = sorted(((p, s) for p, s in ranked if p["topic"] == "general"), key=lambda x: -x[1])
    picked = topic_items[:k]
    for p, _ in general_items:
        if len(picked) >= k:
            break
        picked.append(p)
    return picked


def format_for_prompt(provisions: list[dict]) -> str:
    lines = []
    for p in provisions:
        label = "PRACTICAL GUIDANCE (not a law)" if p["kind"] == "practice" else f"{p['act']}, {p['ref']}"
        caveat = f" Caveat: {p['caveat']}" if p["caveat"] else ""
        lines.append(f"[[{p['id']}]] {label} | {p['title']}: {p['summary']}{caveat}")
    return "\n".join(lines)
