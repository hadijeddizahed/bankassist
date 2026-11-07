from dataclasses import dataclass
import re
from typing import Protocol


@dataclass(frozen=True)
class Document:
    id: str
    text: str


@dataclass(frozen=True)
class Answer:
    text: str
    sources: tuple[str, ...]


class Retriever(Protocol):
    def retrieve(self, question: str) -> list[Document]: ...


class Generator(Protocol):
    def generate(self, question: str, documents: list[Document]) -> str: ...


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
    def generate(self, question: str, documents: list[Document]) -> str:
        return '\n'.join(f'[{d.id}] {d.text}' for d in documents)


class BankAssistant:
    def __init__(self, retriever: Retriever, generator: Generator):
        self.retriever = retriever
        self.generator = generator

    def answer(self, question: str) -> Answer:
        if not question.strip():
            raise ValueError('Please enter a question.')
        documents = self.retriever.retrieve(question)
        if not documents:
            return Answer('I cannot answer from the available policies. Please contact support.', ())
        text = self.generator.generate(question, documents)
        # These are supplied context IDs, not proof that every generated claim is supported.
        return Answer(text, tuple(d.id for d in documents))
