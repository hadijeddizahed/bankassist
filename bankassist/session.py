from dataclasses import dataclass
from typing import Protocol


@dataclass
class Message:
    role: str
    text: str

class SessionStore(Protocol):
    def get_history(self, session_id: str) -> list[Message]: ...
    def add_message(self, session_id: str, role: str, text: str) -> None: ...
    def clear(self, session_id: str) -> None: ...


class InMemorySessionStore(SessionStore):
    """Thread-safe or local memory session store with bounded window."""
    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns
        self._sessions: dict[str, list[Message]] = {}

    def get_history(self, session_id: str) -> list[Message]:
        return list(self._sessions.get(session_id, []))

    def add_message(self, session_id: str, role: str, text: str) -> None:
        if session_id not in self._sessions:
          self._sessions[session_id] = []

        self._sessions[session_id].append(Message(role=role, text=text))
        # Keep only the last max_turns messages (sliding window)
        if len(self._sessions[session_id]) > self.max_turns:
           self._sessions[session_id] = self._sessions[session_id][-self.max_turns:]

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
