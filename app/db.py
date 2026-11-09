import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


def _now():
    return datetime.now(timezone.utc)


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
    language: Mapped[str] = mapped_column(String(16), default="en")
    last_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    case_file: Mapped[dict] = mapped_column(JSON, default=dict)
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", order_by="Message.id", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class Store:
    def __init__(self, url: str):
        kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {"pool_pre_ping": True}
        self.engine = create_engine(url, **kwargs)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(self.engine, expire_on_commit=False)

    def get_or_create(self, conversation_id: str | None) -> Conversation:
        with self.Session() as s:
            conv = s.get(Conversation, conversation_id) if conversation_id else None
            if conv is None:
                conv = Conversation(case_file={})
                s.add(conv)
                s.commit()
            return conv

    def history(self, conversation_id: str, turns: int) -> list[dict]:
        with self.Session() as s:
            rows = s.scalars(
                select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id.desc()).limit(turns * 2)
            ).all()
        return [{"role": r.role, "content": r.content} for r in reversed(rows)]

    def save_turn(self, conversation_id: str, user_text: str, assistant_text: str, meta: dict, case_file: dict, language: str, mode: str):
        with self.Session() as s:
            conv = s.get(Conversation, conversation_id)
            s.add(Message(conversation_id=conversation_id, role="user", content=user_text, meta={}))
            s.add(Message(conversation_id=conversation_id, role="assistant", content=assistant_text, meta=meta))
            conv.case_file = case_file
            conv.language = language
            conv.last_mode = mode
            s.commit()

    def transcript(self, conversation_id: str) -> dict | None:
        with self.Session() as s:
            conv = s.get(Conversation, conversation_id)
            if conv is None:
                return None
            return {
                "id": conv.id,
                "language": conv.language,
                "last_mode": conv.last_mode,
                "case_file": conv.case_file,
                "messages": [{"role": m.role, "content": m.content, "meta": m.meta} for m in conv.messages],
            }
