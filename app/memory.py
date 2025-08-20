import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
from .config import settings

DDL = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role TEXT CHECK(role IN ('user','assistant','system')) NOT NULL,
    content TEXT NOT NULL,
    ts DATETIME NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, ts);
"""

class ConversationMemory:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.sqlite_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self):
        con = sqlite3.connect(self.db_path)
        try:
            cur = con.cursor()
            for stmt in DDL.strip().split(";"):
                if stmt.strip():
                    cur.execute(stmt)
            con.commit()
        finally:
            con.close()

    def add(self, conversation_id: str, role: str, content: str):
        con = sqlite3.connect(self.db_path)
        try:
            con.execute(
                "INSERT INTO messages (conversation_id, role, content, ts) VALUES (?,?,?,?)",
                (conversation_id, role, content, datetime.utcnow().isoformat(timespec="seconds"))
            )
            con.commit()
        finally:
            con.close()

    def fetch(self, conversation_id: str, limit: int = 12) -> List[Tuple[str, str]]:
        con = sqlite3.connect(self.db_path)
        try:
            cur = con.cursor()
            cur.execute(
                "SELECT role, content FROM messages WHERE conversation_id=? ORDER BY ts DESC LIMIT ?",
                (conversation_id, limit),
            )
            rows = cur.fetchall()
            rows.reverse()
            return rows
        finally:
            con.close()

    def format_as_chat(self, conversation_id: str, limit: int = 12) -> str:
        msgs = self.fetch(conversation_id, limit)
        parts = []
        for role, content in msgs:
            if role == "user":
                parts.append(f"사용자: {content}")
            elif role == "assistant":
                parts.append(f"도우미: {content}")
        return "\n".join(parts)
