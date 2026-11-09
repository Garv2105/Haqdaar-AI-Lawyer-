import argparse
import csv
import json
import os
import re
import sys
import tempfile
import time
import traceback
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def parse_args():
    ap = argparse.ArgumentParser(description="Run Haqdaar on the test cases and save unedited raw outputs.")
    ap.add_argument("--cases", default=str(ROOT / "tests" / "cases.yaml"))
    ap.add_argument("--out", default=str(ROOT / "raw_outputs"))
    ap.add_argument("--only", nargs="*", help="case ids to run")
    ap.add_argument("--pause", type=float, default=float(os.getenv("CASE_PAUSE_SECONDS", "20")), help="seconds to wait between turns (free-tier rate limits)")
    ap.add_argument("--scripted", action="store_true", help="use the offline scripted model (pipeline smoke test, not a real run)")
    return ap.parse_args()


def check_case(case, turns):
    exp = case.get("expect", {})
    checks = {}
    first = turns[0]["response"] if turns else {}
    last = turns[-1]["response"] if turns else {}
    if "emergency" in exp:
        checks["emergency_routed"] = (first.get("mode") == "emergency") == exp["emergency"]
    if "topic" in exp:
        topics = [t["response"].get("topic") for t in turns]
        expected = exp["topic"]
        checks["topic"] = expected in topics if expected != "out_of_scope" else any(t["response"].get("mode") == "out_of_scope" for t in turns)
    if "language" in exp:
        from app.lang import detect

        detected = [detect(t["response"].get("reply", "")) for t in turns if t["response"].get("mode") not in ("emergency",)]
        checks["reply_language"] = bool(detected) and detected[0] == exp["language"]
    if "needs_lawyer" in exp:
        checks["lawyer_flag"] = any(t["response"].get("needs_lawyer") for t in turns) == exp["needs_lawyer"]
    if "draft_on_turn" in exp:
        n = exp["draft_on_turn"]
        checks["draft_produced"] = len(turns) >= n and bool(turns[n - 1]["response"].get("draft"))
    if exp.get("no_draft"):
        checks["no_draft"] = not any(t["response"].get("draft") for t in turns)
    if exp.get("no_citations"):
        checks["no_citations"] = not any(t["response"].get("citations") for t in turns)
    if "must_cite_any" in exp:
        cited = {c["id"] for t in turns for c in t["response"].get("citations", [])}
        checks["cites_expected_source"] = bool(cited & set(exp["must_cite_any"]))
    if "must_not_match" in exp:
        text = "\n".join((t["response"].get("reply") or "") + "\n" + (t["response"].get("draft") or "") for t in turns)
        checks["no_forbidden_content"] = not any(re.search(p, text) for p in exp["must_not_match"])
    final_clean = all(t["response"].get("final_guard", {}).get("violations", 0) == 0 for t in turns if t["response"].get("final_guard"))
    checks["final_output_passes_source_check"] = final_clean
    return checks


def to_markdown(case, turns, checks):
    lines = [f"# {case['id']}", "", f"**What this tests:** {case['tests']}", ""]
    for i, t in enumerate(turns, 1):
        r = t["response"]
        lines += [f"## Turn {i}", "", f"**User** (mode sent: {t['mode_sent']}):", "", "> " + t["message"].replace("\n", "\n> "), ""]
        if "error" in t:
            lines += ["**ERROR**", "", "```", t["error"], "```", ""]
            continue
        lines += [
            f"**Haqdaar** (topic: {r.get('topic')}, mode: {r.get('mode')}, language: {r.get('language')}, needs lawyer: {r.get('needs_lawyer')}, {r.get('total_ms')} ms):",
            "",
            r.get("reply", ""),
            "",
        ]
        if r.get("draft"):
            lines += ["**Draft:**", "", "```", r["draft"], "```", ""]
        if r.get("notes"):
            lines += ["**Notes added by the checker:**", ""] + [f"- {n}" for n in r["notes"]] + [""]
        if r.get("citations"):
            lines += ["**Sources:**", ""] + [f"- [{c['n']}] {c['label']} - {c['title']}" for c in r["citations"]] + [""]
        g = r.get("guard", [])
        if g:
            lines += [f"**Source check:** first attempt violations = {g[0].get('violations')}; attempts = {len(g)}; stripped by code after retry = {r.get('final_guard', {}).get('stripped_after_retry', 'n/a')}; violations in what the user saw = {r.get('final_guard', {}).get('violations', 'n/a')}", ""]
            for rep in g:
                if rep.get("violations"):
                    lines += [f"- attempt {rep['attempt']}: invalid ids {rep['invalid_tags']}, unverified refs {rep['unverified_mentions']}, case law {rep['case_law']}"]
            lines += [""]
    lines += ["## Automatic checks", ""] + [f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()]
    return "\n".join(lines) + "\n"


def main():
    args = parse_args()
    db = Path(tempfile.mkdtemp()) / "run.sqlite"
    os.environ["DATABASE_URL"] = f"sqlite:///{db}"
    import app.main as server

    if args.scripted:
        from app.graph import build_graph
        from tests.fakes import ScriptedLLM

        server._engine["graph"] = build_graph(ScriptedLLM(), server.settings)
        model_label = "scripted"
    else:
        server.engine()
        model_label = server._engine["llm"].describe()["main"].replace("/", "_").replace(":", "_")

    cases = yaml.safe_load(open(args.cases, encoding="utf-8"))
    if args.only:
        cases = [c for c in cases if c["id"] in args.only]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = Path(args.out) / f"{stamp}_{model_label}"
    (out_dir / "cases").mkdir(parents=True, exist_ok=True)

    summary_rows = []
    totals = {"input_tokens": 0, "output_tokens": 0, "turns": 0, "ms": 0, "first_attempt_violations": 0, "retries": 0, "stripped": 0}
    for case in cases:
        print(f"Running {case['id']} ...", flush=True)
        conv_id = None
        turns = []
        for turn in case["turns"]:
            mode = turn.get("mode", "auto")
            record = {"message": turn["message"], "mode_sent": mode}
            try:
                r = server.handle(turn["message"], conv_id, mode, turn.get("language", "auto"))
                conv_id = r["conversation_id"]
                record["response"] = r
                totals["turns"] += 1
                totals["ms"] += r.get("total_ms") or 0
                for u in r.get("usage", []):
                    totals["input_tokens"] += u.get("input_tokens", 0)
                    totals["output_tokens"] += u.get("output_tokens", 0)
                g = r.get("guard", [])
                if g:
                    totals["first_attempt_violations"] += 1 if g[0].get("violations") else 0
                    totals["retries"] += max(0, len(g) - 1)
                totals["stripped"] += 1 if r.get("final_guard", {}).get("stripped_after_retry") else 0
            except Exception:
                record["response"] = {}
                record["error"] = traceback.format_exc()
                print(record["error"], flush=True)
            turns.append(record)
            time.sleep(args.pause)
        checks = check_case(case, turns)
        with open(out_dir / "cases" / f"{case['id']}.json", "w", encoding="utf-8") as f:
            json.dump({"case": case, "turns": turns, "checks": checks}, f, ensure_ascii=False, indent=2)
        with open(out_dir / "cases" / f"{case['id']}.md", "w", encoding="utf-8") as f:
            f.write(to_markdown(case, turns, checks))
        passed = sum(checks.values())
        summary_rows.append({"case": case["id"], "passed": passed, "total": len(checks), "failed_checks": ", ".join(k for k, v in checks.items() if not v)})
        print(f"  {passed}/{len(checks)} checks passed", flush=True)

    price_in = float(os.getenv("PRICE_IN_PER_M", "0.15"))
    price_out = float(os.getenv("PRICE_OUT_PER_M", "0.60"))
    cost = totals["input_tokens"] / 1e6 * price_in + totals["output_tokens"] / 1e6 * price_out
    n = max(totals["turns"], 1)
    meta = {
        "run_at": stamp,
        "models": "scripted" if args.scripted else server._engine["llm"].describe(),
        "cases": len(cases),
        "turns": totals["turns"],
        "avg_latency_ms": round(totals["ms"] / n),
        "input_tokens": totals["input_tokens"],
        "output_tokens": totals["output_tokens"],
        "avg_tokens_per_turn": round((totals["input_tokens"] + totals["output_tokens"]) / n),
        "turns_where_first_draft_failed_source_check": totals["first_attempt_violations"],
        "guard_retries": totals["retries"],
        "turns_where_code_stripped_content_after_retry": totals["stripped"],
        "est_cost_usd_at_paid_rates": round(cost, 4),
        "est_cost_usd_per_turn": round(cost / n, 6),
        "price_assumption_per_million_tokens": {"input": price_in, "output": price_out},
    }
    with open(out_dir / "run_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    with open(out_dir / "summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["case", "passed", "total", "failed_checks"])
        w.writeheader()
        w.writerows(summary_rows)
    all_pass = sum(r["passed"] for r in summary_rows)
    all_total = sum(r["total"] for r in summary_rows)
    md = [f"# Run {stamp}", "", f"Models: {meta['models']}", "", f"Checks passed: {all_pass}/{all_total}", ""]
    md += [f"- {k}: {v}" for k, v in meta.items() if k not in ("models",)]
    md += ["", "| case | passed | failed checks |", "|---|---|---|"] + [f"| {r['case']} | {r['passed']}/{r['total']} | {r['failed_checks']} |" for r in summary_rows]
    with open(out_dir / "summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"\nDone. {all_pass}/{all_total} checks passed. Outputs in {out_dir}")


if __name__ == "__main__":
    main()
