import json
import re
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app import guard, knowledge, prompts
from app.lang import detect
from app.llm import Completion, parse_json
from app.screen import EMERGENCY_REPLY, screen

TOPIC_HINTS = {
    "deposit": ["deposit", "landlord", "advance", "pg owner", "kiraya", "makaan malik", "मकान", "किराय", "security"],
    "salary": ["salary", "wages", "tankhwah", "vetan", "pagaar", "hr ", "employer", "full and final", "सैलरी", "वेतन", "तनख्वाह"],
    "consumer": ["refund", "order", "flipkart", "amazon", "airline", "flight", "product", "warranty", "seller", "रिफंड"],
    "notice": ["notice", "legal notice", "cheque", "नोटिस"],
}
VALID_MODES = {"build_case", "explain", "draft", "practise", "explain_notice", "chitchat"}
VALID_TOPICS = {"deposit", "consumer", "salary", "notice", "out_of_scope"}


class TurnState(TypedDict, total=False):
    user_message: str
    history: list[dict]
    case_file: dict
    previous_mode: str
    forced_mode: str
    forced_language: str
    screen: dict
    understanding: dict
    language: str
    topic: str
    mode: str
    sources: list[str]
    generator: str
    raw_answer: str
    attempt: int
    guard_feedback: str
    guard_reports: list[dict]
    reply: str
    draft: str | None
    citations: list[dict]
    notes: list[str]
    needs_lawyer: bool
    lawyer_reasons: list[str]
    final_guard: dict
    trace: list[dict]
    usage: list[dict]


def _merge_case(case: dict, update: dict) -> dict:
    merged = dict(case or {})
    for key in ("other_party", "other_party_type", "location", "goal"):
        value = (update or {}).get(key)
        if value:
            merged[key] = value
    if (update or {}).get("amount_inr"):
        merged["amount_inr"] = update["amount_inr"]
    for key in ("key_dates", "evidence_have", "evidence_missing"):
        items = list(merged.get(key, []))
        for item in (update or {}).get(key, []) or []:
            if item and item not in items:
                items.append(item)
        merged[key] = items
    have = {str(x).lower() for x in merged.get("evidence_have", [])}
    merged["evidence_missing"] = [x for x in merged.get("evidence_missing", []) if str(x).lower() not in have]
    return merged


def _fallback_understanding(text: str, previous_topic: str | None) -> dict:
    low = text.lower()
    scores = {t: sum(h in low for h in hints) for t, hints in TOPIC_HINTS.items()}
    topic = max(scores, key=scores.get) if max(scores.values()) else (previous_topic or "out_of_scope")
    return {
        "language": detect(text),
        "topic": topic,
        "mode": "build_case",
        "needs_lawyer": False,
        "lawyer_reason": "",
        "facts_update": {},
        "missing_info": [],
        "search_query": text[:200],
        "fallback": True,
    }


def _timed(state: TurnState, node: str, start: float):
    state.setdefault("trace", []).append({"node": node, "ms": int((time.perf_counter() - start) * 1000)})


def _log(state: TurnState, step: str, c: Completion):
    state.setdefault("usage", []).append(
        {"step": step, "model": c.model, "input_tokens": c.input_tokens, "output_tokens": c.output_tokens, "latency_ms": c.latency_ms}
    )


def build_graph(llm, settings):
    def screen_node(state: TurnState) -> TurnState:
        t = time.perf_counter()
        result = screen(state["user_message"])
        out = {"screen": {"flags": result.flags, "matches": result.matches, "reasons": result.reasons()}, "trace": list(state.get("trace", []))}
        _timed(out, "screen", t)
        return out

    def emergency_node(state: TurnState) -> TurnState:
        t = time.perf_counter()
        out = {
            "reply": EMERGENCY_REPLY,
            "mode": "emergency",
            "topic": state.get("case_file", {}).get("topic", "unknown"),
            "language": state.get("forced_language") if state.get("forced_language") not in (None, "auto") else detect(state["user_message"]),
            "citations": [],
            "draft": None,
            "notes": [],
            "needs_lawyer": True,
            "lawyer_reasons": state["screen"]["reasons"],
            "guard_reports": [],
            "sources": [],
            "trace": list(state.get("trace", [])),
        }
        _timed(out, "emergency", t)
        return out

    def understand_node(state: TurnState) -> TurnState:
        t = time.perf_counter()
        case = state.get("case_file") or {}
        system = prompts.UNDERSTAND.format(
            previous_mode=state.get("previous_mode") or "none",
            forced_mode=state.get("forced_mode") or "auto",
            forced_language=state.get("forced_language") or "auto",
            case_file=json.dumps(case, ensure_ascii=False),
        )
        usage = list(state.get("usage", []))
        holder = {"usage": usage}
        understanding = None
        user = state["user_message"]
        for attempt in range(2):
            c = llm.complete(system, user, history=state.get("history", []), role="router")
            _log(holder, "understand", c)
            try:
                understanding = parse_json(c.text)
                break
            except ValueError:
                user = state["user_message"] + "\n\n(Return only the JSON object.)"
        if understanding is None:
            understanding = _fallback_understanding(state["user_message"], case.get("topic"))
        topic = understanding.get("topic") if understanding.get("topic") in VALID_TOPICS else _fallback_understanding(state["user_message"], case.get("topic"))["topic"]
        mode = understanding.get("mode") if understanding.get("mode") in VALID_MODES else "build_case"
        if state.get("forced_mode") not in (None, "", "auto"):
            mode = state["forced_mode"]
        previous_topic = case.get("topic")
        if previous_topic in knowledge.TOPICS:
            short_follow_up = len(state["user_message"].split()) < 25 and not state["screen"]["flags"]
            if topic == "out_of_scope" and (mode in ("chitchat", "practise") or short_follow_up):
                topic = previous_topic
            if topic == "notice" and mode == "draft" and previous_topic != "notice":
                topic = previous_topic
        language = state.get("forced_language")
        if language in (None, "", "auto"):
            language = understanding.get("language") or detect(state["user_message"])
        language = language if language in prompts.LANGUAGE_NAMES else detect(state["user_message"])
        new_case = _merge_case(case, understanding.get("facts_update") or {})
        if topic in knowledge.TOPICS:
            new_case["topic"] = topic
        reasons = list(state["screen"]["reasons"])
        if understanding.get("needs_lawyer") and understanding.get("lawyer_reason"):
            reasons.append(understanding["lawyer_reason"])
        out = {
            "understanding": understanding,
            "topic": topic,
            "mode": mode,
            "language": language,
            "case_file": new_case,
            "needs_lawyer": bool(reasons) or bool(understanding.get("needs_lawyer")),
            "lawyer_reasons": reasons,
            "usage": holder["usage"],
            "attempt": 0,
            "guard_reports": [],
            "trace": list(state.get("trace", [])),
        }
        _timed(out, "understand", t)
        return out

    def retrieve_node(state: TurnState) -> TurnState:
        t = time.perf_counter()
        topic = state["topic"] if state["topic"] in knowledge.TOPICS else "notice"
        query = " ".join([state["understanding"].get("search_query", ""), state["user_message"]])
        ids = [p["id"] for p in knowledge.retrieve(topic, query)]
        out = {"sources": ids, "trace": list(state.get("trace", []))}
        _timed(out, "retrieve", t)
        return out

    def _resources(topic: str) -> str:
        items = knowledge.resources_for(topic) + [r for r in knowledge.resources_for("general") if r not in knowledge.resources_for(topic)]
        return "; ".join(f"{r['name']}: {r['contact'] or r['url']}" + (f" ({r['url']})" if r["contact"] and r["url"] else "") for r in items)

    def respond_node(state: TurnState) -> TurnState:
        t = time.perf_counter()
        mode = state["mode"]
        ids = state.get("sources", []) if mode != "chitchat" else []
        corpus = knowledge.provisions_by_id()
        lawyer_note = "; ".join(state.get("lawyer_reasons", [])) or "none"
        system = prompts.SYSTEM.format(
            language_name=prompts.LANGUAGE_NAMES.get(state["language"], "English"),
            topic=state["topic"],
            case_file=json.dumps(state.get("case_file", {}), ensure_ascii=False),
            missing_info=json.dumps(state["understanding"].get("missing_info", []), ensure_ascii=False),
            lawyer_note=lawyer_note,
            sources=knowledge.format_for_prompt([corpus[i] for i in ids]) or "(none)",
            resources=_resources(state["topic"] if state["topic"] in knowledge.TOPICS else "general"),
            mode_instructions=prompts.MODE_INSTRUCTIONS[mode],
        )
        if state.get("guard_feedback"):
            system += prompts.RETRY_SUFFIX.format(feedback=state["guard_feedback"])
        holder = {"usage": list(state.get("usage", []))}
        c = llm.complete(system, state["user_message"], history=state.get("history", []), role="main")
        _log(holder, f"respond:{mode}", c)
        out = {"raw_answer": guard.normalize_tags(c.text), "generator": "respond", "usage": holder["usage"], "trace": list(state.get("trace", []))}
        _timed(out, f"respond:{mode}", t)
        return out

    def out_of_scope_node(state: TurnState) -> TurnState:
        t = time.perf_counter()
        reason = "; ".join(state.get("lawyer_reasons", [])) or state["understanding"].get("lawyer_reason") or "it is not one of the problem types covered"
        system = prompts.OUT_OF_SCOPE.format(reason=reason, language_name=prompts.LANGUAGE_NAMES.get(state["language"], "English"))
        if state.get("guard_feedback"):
            system += prompts.RETRY_SUFFIX.format(feedback=state["guard_feedback"])
        holder = {"usage": list(state.get("usage", []))}
        c = llm.complete(system, state["user_message"], history=state.get("history", []), role="main")
        _log(holder, "out_of_scope", c)
        out = {
            "raw_answer": guard.normalize_tags(c.text),
            "generator": "out_of_scope",
            "sources": [],
            "mode": "out_of_scope",
            "needs_lawyer": True,
            "usage": holder["usage"],
            "trace": list(state.get("trace", [])),
        }
        _timed(out, "out_of_scope", t)
        return out

    def guard_node(state: TurnState) -> TurnState:
        t = time.perf_counter()
        report = guard.check(state["raw_answer"], state.get("sources", []))
        reports = list(state.get("guard_reports", [])) + [{"attempt": state.get("attempt", 0), **report.as_dict()}]
        out = {"guard_reports": reports, "trace": list(state.get("trace", []))}
        if report.violations and state.get("attempt", 0) < settings.max_guard_retries:
            out["attempt"] = state.get("attempt", 0) + 1
            out["guard_feedback"] = report.feedback()
        else:
            out["guard_feedback"] = ""
        _timed(out, "guard", t)
        return out

    def finalize_node(state: TurnState) -> TurnState:
        t = time.perf_counter()
        ids = state.get("sources", [])
        report = guard.check(state["raw_answer"], ids)
        cleaned = guard.enforce(state["raw_answer"], ids, report)
        body, draft = guard.split_draft(cleaned)
        body, citations = guard.render_citations(body, ids)
        if draft:
            draft_tags = guard.TAG.findall(draft)
            _, draft_cites = guard.render_citations(" ".join(f"[[{x}]]" for x in draft_tags), ids)
            known = {c["id"] for c in citations}
            for c in draft_cites:
                if c["id"] not in known:
                    c["n"] = len(citations) + 1
                    citations.append(c)
            draft = guard.render_inline(draft, ids).replace("**", "")
            draft = re.sub(r"^#+\s*", "", draft, flags=re.MULTILINE)
        shown = guard.check(cleaned, ids).as_dict()
        shown["stripped_after_retry"] = report.violations
        out = {
            "reply": body,
            "draft": draft,
            "citations": citations,
            "notes": guard.outdated_notes(report),
            "final_guard": shown,
            "trace": list(state.get("trace", [])),
        }
        _timed(out, "finalize", t)
        return out

    def after_screen(state: TurnState) -> str:
        return "emergency" if "emergency" in state["screen"]["flags"] else "understand"

    def after_understand(state: TurnState) -> str:
        if state["mode"] == "chitchat":
            return "respond"
        if state["topic"] == "out_of_scope":
            return "out_of_scope"
        return "retrieve"

    def after_guard(state: TurnState) -> str:
        if state.get("guard_feedback"):
            return state.get("generator", "respond")
        return "finalize"

    g = StateGraph(TurnState)
    g.add_node("screen", screen_node)
    g.add_node("emergency", emergency_node)
    g.add_node("understand", understand_node)
    g.add_node("retrieve", retrieve_node)
    g.add_node("respond", respond_node)
    g.add_node("out_of_scope", out_of_scope_node)
    g.add_node("guard", guard_node)
    g.add_node("finalize", finalize_node)
    g.add_edge(START, "screen")
    g.add_conditional_edges("screen", after_screen, {"emergency": "emergency", "understand": "understand"})
    g.add_edge("emergency", END)
    g.add_conditional_edges("understand", after_understand, {"respond": "respond", "out_of_scope": "out_of_scope", "retrieve": "retrieve"})
    g.add_edge("retrieve", "respond")
    g.add_edge("respond", "guard")
    g.add_edge("out_of_scope", "guard")
    g.add_conditional_edges("guard", after_guard, {"respond": "respond", "out_of_scope": "out_of_scope", "finalize": "finalize"})
    g.add_edge("finalize", END)
    return g.compile()


def run_turn(app, *, message: str, history: list[dict], case_file: dict, previous_mode: str | None, forced_mode: str = "auto", forced_language: str = "auto") -> dict[str, Any]:
    start = time.perf_counter()
    state = app.invoke(
        {
            "user_message": message,
            "history": history,
            "case_file": case_file or {},
            "previous_mode": previous_mode or "none",
            "forced_mode": forced_mode or "auto",
            "forced_language": forced_language or "auto",
        }
    )
    state["total_ms"] = int((time.perf_counter() - start) * 1000)
    return state
