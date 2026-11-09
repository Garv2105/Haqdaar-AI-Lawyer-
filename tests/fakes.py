import json
import re

from app.llm import Completion


class ScriptedLLM:
    def __init__(self, hallucinate_first: bool = True):
        self.hallucinate_first = hallucinate_first
        self.calls = []

    def describe(self):
        return {"main": "scripted:main", "router": "scripted:router"}

    def complete(self, system, user, history=None, role="main"):
        self.calls.append({"role": role, "system": system, "user": user})
        if "return ONE JSON object" in system:
            return Completion(text=json.dumps(self._understand(user)), model="scripted:router", input_tokens=900, output_tokens=150, latency_ms=5)
        if "outside what you can help with" in system:
            return Completion(text="This needs a lawyer. Call 15100 for free legal aid.", model="scripted:main", input_tokens=300, output_tokens=40, latency_ms=5)
        ids = re.findall(r"^\[\[([A-Z0-9\-]+)\]\]", system, flags=re.MULTILINE)
        first = ids[0] if ids else ""
        retry = "FAILED THE SOURCE CHECK" in system
        if "Draft the document" in system:
            body = f"Here is your notice.\n=== DRAFT START ===\nTo: [FILL: landlord name]\nYou must refund Rs 30,000 [[{first}]].\n=== DRAFT END ===\nHave a lawyer check this."
        else:
            body = f"You have a strong case [[{first}]]."
        if self.hallucinate_first and not retry:
            body += " Also see [[FAKE-999]] and Section 420 of the Indian Penal Code. In Sharma v. State of Delhi the court agreed."
        return Completion(text=body, model="scripted:main", input_tokens=2500, output_tokens=300, latency_ms=5)

    def _understand(self, user):
        low = user.lower()
        topic = "out_of_scope"
        if "deposit" in low or "landlord" in low:
            topic = "deposit"
        elif "salary" in low:
            topic = "salary"
        elif "refund" in low:
            topic = "consumer"
        elif "notice" in low:
            topic = "notice"
        mode = "draft" if "draft" in low else "explain"
        return {
            "language": "en",
            "topic": topic,
            "mode": mode,
            "needs_lawyer": False,
            "lawyer_reason": "",
            "facts_update": {"other_party": "landlord" if topic == "deposit" else "", "amount_inr": 30000, "key_dates": [], "evidence_have": ["rent agreement"], "evidence_missing": ["move-out photos"], "goal": "get money back"},
            "missing_info": ["city"],
            "search_query": user[:80],
        }
