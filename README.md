# Haqdaar

An AI legal helper for everyday problems in India. You tell it what happened (typed or spoken, in your own language) and it helps you act on it:

- **Build my case:** turns a messy story into a timeline, the proof you have, and the proof you still need
- **Where do I stand?:** your rights and your options, from easiest to hardest, with deadlines
- **Draft:** a legal notice, a consumer complaint, or a complaint to the labour authority, with blanks for anything it does not know
- **Practise:** it plays the landlord, HR manager or customer care agent so you can rehearse, and coaches you after each reply
- **Explain a notice I got:** what the notice says, the deadline, and what to do

**What it covers:** security deposits, consumer refunds (including e-commerce), unpaid or late salary, and legal notices you received (including cheque bounce).
**What it does not cover:** it refers these to a lawyer and the free legal aid helpline (15100): criminal, police, family, land and inheritance matters, tax, and business-to-business disputes.

## How it avoids making up law

1. **A closed source list.** Every legal statement must come from `app/data/provisions.json`. This is 25 provisions and practical tips, each checked by hand against current sources on 9 Nov 2026, with a plain-language summary and a caveat. The model only sees the provisions retrieved for the current topic, and it must cite them by id, for example `[[COW2019-S17]]`.
2. **A checker in code, not in the prompt.** `app/guard.py` reads every answer and flags:
   - ids that were not supplied
   - any "Section / Article / Rule / धारा N" whose act and number are not in the supplied sources
   - anything that looks like case law (case names, AIR / SCC citations, "the Supreme Court held")
   - repealed laws (IPC, CrPC, Payment of Wages Act, CPA 1986, e-Daakhil)

   A failed answer is sent back to the model once with the reasons. Anything still wrong is removed before the user sees it, and the removal is logged.
3. **No case law, ever.** The bot is not allowed to cite judgments, because that is where models invent the most.
4. **Safety first.** A rule-based screen runs before any model call. Threats, violence or self-harm go straight to fixed helpline text (112, 181, 14416, 15100). Police, family and land matters are flagged for a lawyer.

## Architecture

```
message ─► screen (rules) ─┬─► emergency reply (fixed text, no LLM)
                           └─► understand (router LLM, JSON: language, topic, mode, facts)
                                   ├─► out of scope ─► referral reply ──┐
                                   └─► retrieve (BM25 over the verified sources)
                                           └─► respond (main LLM, mode prompt) ──► guard ─► retry once ─► finalize
                                                                                     (strip, number citations, split draft)
```

- LangGraph runs the turn. FastAPI serves the API and the web page. Postgres (or SQLite) stores conversations and the case file.
- The two model roles (router and main) are set in `.env`. Groq, Gemini, OpenRouter, OpenAI, Anthropic, Ollama or any OpenAI-compatible endpoint can be used without code changes.
- Voice uses the browser's built-in speech recognition and read-aloud (Chrome or Edge), so it costs nothing and supports Indian languages.

## Run it

**1. Get a free key.** Create one at https://console.groq.com/keys, then:

```bash
cp .env.example .env        # paste the key into LLM_API_KEY and ROUTER_API_KEY
```

**2a. With Docker (app + Postgres):**

```bash
docker compose up --build
```

Then open http://localhost:8000.

**2b. Without Docker (uses SQLite):**

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Deploy free on Hugging Face Spaces:**
1. Create a Docker Space and push this repo.
2. Add `app_port: 8000` to the Space README header.
3. Add `LLM_API_KEY` and `ROUTER_API_KEY` as Space secrets.

It runs on SQLite there.

## Generate the raw outputs

```bash
python -m tests.run_cases
```

This runs the 16 test cases in `tests/cases.yaml` (23 turns: English, Hindi, Hinglish and Tamil, emergencies, out-of-scope requests, a demand for case law, a prompt injection, a repealed-law trap). For each case it writes a JSON file (full trace: guard reports, tokens, latency) and a Markdown transcript to `raw_outputs/<timestamp>_<model>/`, plus `summary.md` with the automatic checks and an estimated cost. It waits 20 s between turns to stay inside Groq's free-tier limits, so expect about 10 minutes.

Useful options:
- `--only C08_notice_cheque_bounce_received` runs a single case.
- `--scripted` is an offline smoke test with a fake model.

Unit tests, which need no API key:

```bash
python -m pytest -q
```

## API

- `POST /api/chat` with `{message, conversation_id?, mode?, language?}` returns the reply, the draft, citations, flags, the case file, guard reports, tokens and timings.
- `GET /api/conversation/{id}` returns the full transcript and the case file.
- `GET /api/coverage` lists what the bot knows.
- `GET /api/health` returns the active models and the database.

## Known limits

- It knows 25 provisions, not Indian law in general. Anything outside them gets "I'm not sure, ask a lawyer".
- Rent law is state-specific. The Model Tenancy Act binds only states that adopted it, and the bot says so, but it has no state rent acts.
- The citation check matches act names and section numbers, not meaning. A correct section can still be paraphrased wrongly. The summaries are kept short to reduce this risk, and a lawyer should check any notice before it is sent.
- The case-law filter is pattern-based, so it can miss unusual formats or remove a harmless sentence containing "vs.".
- Browser voice input quality depends on the browser and language. Some languages have no read-aloud voice on some devices.
