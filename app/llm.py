import json
import os
import re
import time
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.config import ModelSettings

OPENAI_COMPATIBLE = {
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "ollama": "http://localhost:11434/v1",
    "openai": None,
    "openai_compatible": None,
}

KEY_ENV = {
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


@dataclass
class Completion:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0


@dataclass
class UsageLog:
    calls: list = field(default_factory=list)

    def add(self, step: str, completion: Completion):
        self.calls.append(
            {
                "step": step,
                "model": completion.model,
                "input_tokens": completion.input_tokens,
                "output_tokens": completion.output_tokens,
                "latency_ms": completion.latency_ms,
            }
        )


def build_chat_model(cfg: ModelSettings):
    provider = cfg.provider
    api_key = cfg.api_key or os.getenv(KEY_ENV.get(provider, ""), None)
    if provider in OPENAI_COMPATIBLE:
        from langchain_openai import ChatOpenAI

        base_url = cfg.base_url or OPENAI_COMPATIBLE[provider]
        return ChatOpenAI(
            model=cfg.model,
            api_key=api_key or "not-needed",
            base_url=base_url,
            temperature=cfg.temperature,
            max_retries=4,
            timeout=90,
        )
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=cfg.model, google_api_key=api_key, temperature=cfg.temperature, max_retries=4)
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=cfg.model, api_key=api_key, temperature=cfg.temperature, max_retries=4, max_tokens=2048)
    raise ValueError(f"Unknown LLM provider '{provider}'. Use one of: groq, openrouter, ollama, openai, openai_compatible, gemini, anthropic.")


def _to_messages(system: str, history: list[dict], user: str):
    messages = [SystemMessage(content=system)]
    for turn in history:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    messages.append(HumanMessage(content=user))
    return messages


def _text_of(message) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
        elif isinstance(block, str):
            parts.append(block)
    return "".join(parts)


class LLM:
    def __init__(self, main: ModelSettings, router: ModelSettings):
        self.settings = {"main": main, "router": router}
        self.models = {"main": build_chat_model(main), "router": build_chat_model(router)}

    def describe(self) -> dict:
        return {role: f"{cfg.provider}:{cfg.model}" for role, cfg in self.settings.items()}

    def complete(self, system: str, user: str, history: list[dict] | None = None, role: str = "main") -> Completion:
        model = self.models[role]
        start = time.perf_counter()
        response = model.invoke(_to_messages(system, history or [], user))
        latency = int((time.perf_counter() - start) * 1000)
        usage = getattr(response, "usage_metadata", None) or {}
        return Completion(
            text=_text_of(response).strip(),
            model=self.describe()[role],
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            latency_ms=latency,
        )


def parse_json(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        return json.loads(cleaned[start : end + 1])
    raise ValueError("No JSON object found in model output")
