import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import BASE_DIR, load_settings
from app.db import Store
from app.graph import build_graph, run_turn
from app.knowledge import coverage

settings = load_settings()
store = Store(settings.database_url)
app = FastAPI(title="Haqdaar", version="1.0")
_engine = {}


def engine():
    if "graph" not in _engine:
        from app.llm import LLM

        llm = LLM(settings.main, settings.router)
        _engine["llm"] = llm
        _engine["graph"] = build_graph(llm, settings)
    return _engine["graph"]


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = None
    mode: str = "auto"
    language: str = "auto"


def handle(message: str, conversation_id: str | None, mode: str, language: str) -> dict:
    conv = store.get_or_create(conversation_id)
    history = store.history(conv.id, settings.history_turns)
    state = run_turn(
        engine(),
        message=message,
        history=history,
        case_file=conv.case_file or {},
        previous_mode=conv.last_mode,
        forced_mode=mode,
        forced_language=language,
    )
    assistant_text = state["reply"] + (f"\n\n{state['draft']}" if state.get("draft") else "")
    meta = {
        "mode": state.get("mode"),
        "topic": state.get("topic"),
        "citations": state.get("citations", []),
        "flags": state.get("screen", {}).get("flags", []),
        "guard": state.get("guard_reports", []),
        "draft": state.get("draft"),
        "needs_lawyer": state.get("needs_lawyer", False),
    }
    store.save_turn(conv.id, message, assistant_text, meta, state.get("case_file", conv.case_file or {}), state.get("language", "en"), state.get("mode"))
    return {
        "conversation_id": conv.id,
        "reply": state["reply"],
        "draft": state.get("draft"),
        "citations": state.get("citations", []),
        "notes": state.get("notes", []),
        "mode": state.get("mode"),
        "topic": state.get("topic"),
        "language": state.get("language"),
        "needs_lawyer": state.get("needs_lawyer", False),
        "lawyer_reasons": state.get("lawyer_reasons", []),
        "flags": state.get("screen", {}).get("flags", []),
        "case_file": state.get("case_file", conv.case_file),
        "guard": state.get("guard_reports", []),
        "final_guard": state.get("final_guard", {}),
        "sources_offered": state.get("sources", []),
        "usage": state.get("usage", []),
        "trace": state.get("trace", []),
        "total_ms": state.get("total_ms"),
    }


@app.post("/api/chat")
def chat(body: ChatIn):
    return handle(body.message, body.conversation_id, body.mode, body.language)


@app.get("/api/conversation/{conversation_id}")
def conversation(conversation_id: str):
    data = store.transcript(conversation_id)
    if data is None:
        raise HTTPException(404, "Conversation not found")
    return data


@app.get("/api/coverage")
def get_coverage():
    return coverage()


@app.get("/api/health")
def health():
    return {"ok": True, "models": {"main": f"{settings.main.provider}:{settings.main.model}", "router": f"{settings.router.provider}:{settings.router.model}"}, "database": settings.database_url.split(":")[0]}


static_dir = Path(BASE_DIR) / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def index():
    return FileResponse(static_dir / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
