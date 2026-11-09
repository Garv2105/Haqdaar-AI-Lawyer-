from app import guard, knowledge
from app.config import load_settings
from app.graph import build_graph, run_turn
from app.lang import detect
from app.screen import screen
from tests.fakes import ScriptedLLM


def test_corpus_ids_unique_and_complete():
    provisions = knowledge.load_corpus()["provisions"]
    ids = [p["id"] for p in provisions]
    assert len(ids) == len(set(ids))
    for p in provisions:
        for key in ("id", "topic", "kind", "act", "ref", "numbers", "title", "summary", "caveat", "keywords", "source"):
            assert key in p


def test_retrieval_prefers_topic():
    ids = [p["id"] for p in knowledge.retrieve("salary", "salary not paid after resignation")]
    assert ids[0].startswith("COW2019")
    assert "COW2019-S17" in ids


def test_guard_flags_fabrications():
    allowed = ["CPA2019-S69", "CPA2019-S34"]
    text = (
        "You have 2 years [[CPA2019-S69]]. File under Section 34 of the Consumer Protection Act. "
        "Also Section 12 of the Consumer Protection Act helps [[CPA2019-S99]]. "
        "In Sharma v. State of Delhi the court agreed. See AIR 2005 SC 123."
    )
    r = guard.check(text, allowed)
    assert r.valid_tags == ["CPA2019-S69"]
    assert r.invalid_tags == ["CPA2019-S99"]
    assert any("12" in m for m in r.unverified_mentions)
    assert not any("34" in m for m in r.unverified_mentions)
    assert r.case_law
    cleaned = guard.enforce(text, allowed, r)
    assert "CPA2019-S99" not in cleaned and "Sharma" not in cleaned and "AIR 2005" not in cleaned
    assert "Section 34" in cleaned


def test_guard_ignores_order_numbers_and_fill_placeholders():
    r = guard.check("My order 40981 was cancelled. [FILL: Section of agreement] Rs. 4,500 paid.", ["CPA2019-S69"])
    assert r.violations == 0


def test_guard_flags_outdated_law():
    r = guard.check("Under the Payment of Wages Act you can claim.", ["COW2019-S17"])
    assert "COW2019-S69" in r.outdated


def test_unicode_and_single_bracket_ids_are_normalized():
    raw = "Refund rule [[MTA2021\u2011S11]] and limit [LIM1963\u2013A113] and bogus [[ipc\u2011420]]."
    text = guard.normalize_tags(raw)
    assert "[[MTA2021-S11]]" in text and "[[LIM1963-A113]]" in text and "[[IPC-420]]" in text
    r = guard.check(text, ["MTA2021-S11", "LIM1963-A113"])
    assert r.valid_tags == ["MTA2021-S11", "LIM1963-A113"] and r.invalid_tags == ["IPC-420"]
    rendered, cites = guard.render_citations(guard.enforce(text, ["MTA2021-S11", "LIM1963-A113"], r), ["MTA2021-S11", "LIM1963-A113"])
    assert "[[" not in rendered and len(cites) == 2


def test_render_citations_numbers_in_order():
    text, cites = guard.render_citations("A [[COW2019-S45]] B [[COW2019-S17]] C [[COW2019-S45]]", ["COW2019-S17", "COW2019-S45"])
    assert text == "A [1] B [2] C [1]"
    assert [c["id"] for c in cites] == ["COW2019-S45", "COW2019-S17"]


def test_screen_flags():
    assert "emergency" in screen("My landlord threatened to kill me").flags
    assert "criminal" in screen("police ne FIR nahi likhi").flags
    assert "family" in screen("I want a divorce").flags
    assert screen("My landlord kept my deposit of Rs 30000").flags == []
    assert screen("I will tell my father about the deposit").flags == []


def test_router_language_is_checked_against_script():
    from app.lang import reconcile
    assert reconcile("hi", "Give me the exact section that says he must pay 18% interest") == "en"
    assert reconcile("hi", "meri shaadi ko 3 saal hue hain, husband ke saath nahi rehna, divorce kaise milega") == "hinglish"
    assert reconcile("en", "मेरी सैलरी नहीं मिली") == "hi"
    assert reconcile("hinglish", "mera deposit wapas nahi mila") == "hinglish"
    assert reconcile("mr", "माझा पगार मिळाला नाही आहे") == "mr"


def test_eviction_threat_flags_lawyer():
    assert "eviction" in screen("he says I must vacate in 15 days or he will file an eviction suit").flags
    assert not screen("he will file an eviction suit").out_of_scope


def test_language_detection():
    assert detect("मेरा मकान मालिक डिपॉज़िट नहीं लौटा रहा") == "hi"
    assert detect("mera landlord deposit wapas nahi de raha hai") == "hinglish"
    assert detect("My landlord is not returning my deposit") == "en"
    assert detect("என் சம்பளம் வரவில்லை") == "ta"


def test_graph_strips_hallucinations_after_retry():
    llm = ScriptedLLM(hallucinate_first=True)
    app = build_graph(llm, load_settings())
    state = run_turn(app, message="My landlord kept my deposit of Rs 30000, what are my rights?", history=[], case_file={}, previous_mode=None)
    assert state["topic"] == "deposit"
    assert len(state["guard_reports"]) == 2
    assert state["guard_reports"][0]["violations"] > 0
    assert state["guard_reports"][1]["violations"] == 0
    assert "FAKE-999" not in state["reply"] and "Sharma" not in state["reply"]
    assert state["citations"]


def test_graph_strips_even_if_model_keeps_hallucinating(monkeypatch):
    class Stubborn(ScriptedLLM):
        def complete(self, system, user, history=None, role="main"):
            c = super().complete(system, user, history, role)
            if "FAILED THE SOURCE CHECK" in system:
                c.text += " See [[FAKE-1]] and Section 999 of the Contract Act."
            return c

    app = build_graph(Stubborn(), load_settings())
    state = run_turn(app, message="landlord deposit draft a notice", history=[], case_file={}, previous_mode=None)
    assert "FAKE-1" not in state["reply"] and "999" not in state["reply"]
    assert state["draft"] and "[FILL: landlord name]" in state["draft"]
    assert state["final_guard"]["stripped_after_retry"] > 0
    assert state["final_guard"]["violations"] == 0


def test_emergency_short_circuits():
    llm = ScriptedLLM()
    app = build_graph(llm, load_settings())
    state = run_turn(app, message="my landlord is beating me and locked me inside", history=[], case_file={}, previous_mode=None)
    assert state["mode"] == "emergency" and "112" in state["reply"]
    assert llm.calls == []


def test_flagged_out_of_scope_chitchat_still_routes_to_referral():
    class Chatty(ScriptedLLM):
        def _understand(self, user):
            d = super()._understand(user)
            d.update({"topic": "out_of_scope", "mode": "chitchat", "language": "hi"})
            return d

    app = build_graph(Chatty(), load_settings())
    state = run_turn(app, message="divorce kaise milega aur bachche ki custody?", history=[], case_file={}, previous_mode=None)
    assert state["mode"] == "out_of_scope" and state["language"] == "hinglish"


def test_out_of_scope_routes_to_lawyer():
    app = build_graph(ScriptedLLM(), load_settings())
    state = run_turn(app, message="I want to file for divorce", history=[], case_file={}, previous_mode=None)
    assert state["mode"] == "out_of_scope" and state["needs_lawyer"]
    assert state["citations"] == []
