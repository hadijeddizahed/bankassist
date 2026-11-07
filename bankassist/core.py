from dataclasses import dataclass
import re
from typing import Protocol, Any

from bankassist.session import Message, SessionStore


@dataclass(frozen=True)
class Document:
    id: str
    text: str


@dataclass(frozen=True)
class Answer:
    text: str
    sources: tuple[str, ...]
    prompt_version: str = "v1.0.0"
    model_id: str = "offline"
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0


class Retriever(Protocol):
    def retrieve(self, question: str) -> list[Document]: ...


class Generator(Protocol):
    def generate(self, question: str, documents: list[Document], history: list[Message] | None = None) -> Any: ...


class KeywordRetriever:
    """Day-2 baseline, NOT embeddings or vector search. Replace on days 4-5."""
    STOP = {'a', 'an', 'the', 'is', 'are', 'how', 'what', 'my', 'i', 'to', 'for', 'do', 'can'}

    def __init__(self, documents: list[Document]):
        self.documents = documents

    def tokens(self, text: str) -> set[str]:
        return set(re.findall(r'[a-z]+', text.lower())) - self.STOP

    def retrieve(self, question: str) -> list[Document]:
        query = self.tokens(question)
        ranked = sorted(self.documents, key=lambda d: len(query & self.tokens(d.text)), reverse=True)
        return [d for d in ranked if query & self.tokens(d.text)][:2]


class ExtractiveGenerator:
    """Offline smoke-test adapter. Quotes policies; does not call an LLM."""
    def generate(self, question: str, documents: list[Document],  history: list[Message] | None = None,) -> str:
        return '\n'.join(f'[{d.id}] {d.text}' for d in documents)


class BankAssistant:
    def __init__(self, retriever: Retriever, generator: Generator, session_store: SessionStore | None = None):
        self.retriever = retriever
        self.generator = generator
        self.session_store = session_store

    def answer(self, question: str, session_id: str | None = None) -> Answer:
        cleaned = question.strip()
        if not cleaned:
            raise ValueError('Please enter a question.')
        history: list[Message] = []
        if self.session_store and session_id:
            history = self.session_store.get_history(session_id)

        documents = self.retriever.retrieve(question)
        if not documents:
            ans_text = "I cannot answer from the available policies. Please contact support."
            if self.session_store and session_id:
                self.session_store.add_message(session_id, "user", cleaned)
                self.session_store.add_message(session_id, "assistant", ans_text)
            return Answer(text=ans_text, sources=())
        result = self.generator.generate(cleaned, documents, history=history)

        if hasattr(result, 'text'):
            text = result.text
            prompt_version = result.prompt_version
            model_id = result.model_id
            in_tokens = result.input_tokens
            out_tokens = result.output_tokens
            lat = result.latency_ms
        else:
            text = str(result)
            prompt_version = "v1.0.0"
            model_id = "extractive"
            in_tokens = out_tokens = 0
            lat = 0.0
        if self.session_store and session_id:
            self.session_store.add_message(session_id, "user", cleaned)
            self.session_store.add_message(session_id, "assistant", text)
        return Answer(
            text=text,
            sources=tuple(d.id for d in documents),
            prompt_version=prompt_version,
            model_id=model_id,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            latency_ms=lat,
        )




