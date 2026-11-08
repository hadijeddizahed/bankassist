from dataclasses import dataclass
import re
from typing import Any
from bankassist.core import Document, Retriever
from bankassist.session import Message, SessionStore

ABSTENTION_MESSAGE = "I cannot answer from the available policies. Please contact support."


@dataclass(frozen=True)
class RAGResult:
    text: str
    retrieved_sources: tuple[str, ...]
    cited_sources: tuple[str, ...]
    is_abstention: bool
    model_id: str
    prompt_version: str
    latency_ms: int


class RAGPipeline:
    """End-to-End RAG orchestrator with citation provenance verification."""

    def __init__(
            self,
            retriever: Retriever,
            generator: Any,
            session_store: SessionStore | None = None,
    ):
        self.retriever = retriever
        self.generator = generator
        self.session_store = session_store

    @staticmethod
    def extract_citations(text: str) -> list[str]:
        """Finds all occurrences of [POL-XXX] in the output text."""
        return sorted(list(set(re.findall(r"\[(POL-\d+)]", text))))

    @staticmethod
    def contextualize_query(question: str, history: list[Message]) -> str:
        """If there is conversation history, contextualize pronouns/ellipses
        into a standalone search query for the vector database.
        """
        if not history:
            return question

        q_lower = question.lower()
        follow_up_triggers = ["it", "that", "this", "they", "them", "what about", "how about", "and ", "one"]
        if any(trigger in q_lower for trigger in follow_up_triggers):
            for prev in reversed(history):
                if prev.role == "user":
                    return f"{question} (context: {prev.text})"

        return question

    def run(self, question: str, session_id: str | None = None) -> RAGResult:
        cleaned = question.strip()
        if not cleaned:
            raise ValueError("Please enter a question.")

        history: list[Message] = []
        if self.session_store and session_id:
            history = self.session_store.get_history(session_id)

        # Contextualize query with conversation history before vector search
        search_query = self.contextualize_query(cleaned, history)
        documents = self.retriever.retrieve(search_query)
        retrieved_ids = tuple(d.id for d in documents)

        # 2. If no documents pass similarity threshold, abstain immediately
        if not documents:
            if self.session_store and session_id:
                self.session_store.add_message(session_id, "user", cleaned)
                self.session_store.add_message(session_id, "assistant", ABSTENTION_MESSAGE)
            return RAGResult(
                text=ABSTENTION_MESSAGE,
                retrieved_sources=(),
                cited_sources=(),
                is_abstention=True,
                model_id="rule-abstention",
                prompt_version="v1.0.0",
                latency_ms=0.0,
            )

        # 3. Generate grounded answer
        gen_output = self.generator.generate(cleaned, documents, history=history)
        if hasattr(gen_output, "text"):
            raw_text = gen_output.text
            model_id = gen_output.model_id
            prompt_version = gen_output.prompt_version
            latency_ms = gen_output.latency_ms
        else:
            raw_text = str(gen_output)
            model_id = "default"
            prompt_version = "v1.0.0"
            latency_ms = 0.0
        # Check if model or rules chose to abstain
        is_abstention = (
                ABSTENTION_MESSAGE.lower() in raw_text.lower()
                or "cannot answer" in raw_text.lower()
        )
        # 4. Extract citations and verify provenance
        cited = self.extract_citations(raw_text)
        # Ensure cited IDs actually exist in retrieved_ids
        valid_citations = tuple(c for c in cited if c in retrieved_ids)
        if self.session_store and session_id:
            self.session_store.add_message(session_id, "user", cleaned)
            self.session_store.add_message(session_id, "assistant", raw_text)
        return RAGResult(
            text=raw_text,
            retrieved_sources=retrieved_ids,
            cited_sources=valid_citations,
            is_abstention=is_abstention,
            model_id=model_id,
            prompt_version=prompt_version,
            latency_ms=latency_ms,
        )







