import json
from pathlib import Path
from bankassist.core import Document
from bankassist.generator import MockLLMGenerator
from bankassist.rag import RAGPipeline, ABSTENTION_MESSAGE
from bankassist.retriever import QdrantVectorRetriever, SimpleHashEmbedder


def load_policies() -> list[Document]:
    path = Path(__file__).resolve().parent.parent / "data" / "policies.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Document(id=d["id"], text=d["text"]) for d in data]


def get_rag_pipeline(score_threshold: float = 0.18) -> RAGPipeline:
    docs = load_policies()
    embedder = SimpleHashEmbedder(dim=256)
    retriever = QdrantVectorRetriever(
        embedder=embedder,
        location=":memory:",
        score_threshold=score_threshold,
    )
    retriever.index_documents(docs)
    generator = MockLLMGenerator(model_id="mock-llm-v1")
    return RAGPipeline(retriever=retriever, generator=generator)


def test_supported_questions_cite_and_ground():
    rag = get_rag_pipeline()

    supported_cases = [
        ("How do I report a lost card?", "POL-001"),
        ("What is the basic account monthly fee?", "POL-002"),
        ("When do domestic wire transfers process?", "POL-005"),
        ("How does overdraft protection work?", "POL-006"),
        ("What is the minimum balance for high-yield savings?", "POL-009"),
    ]

    for question, expected_id in supported_cases:
        result = rag.run(question)
        assert not result.is_abstention, f"Expected answer for '{question}', got abstention"
        assert expected_id in result.retrieved_sources
        assert expected_id in result.cited_sources


def test_unsupported_questions_abstain_cleanly():
    rag = get_rag_pipeline()

    unsupported_cases = [
        "What is your mortgage interest rate?",
        "Can I buy Bitcoin with my checking account?",
        "What are the trading hours for the Tokyo stock exchange?",
        "How do I apply for a personal car loan?",
        "What is the weather forecast in London today?",
    ]

    for question in unsupported_cases:
        result = rag.run(question)
        assert result.is_abstention, f"Expected abstention for '{question}', got: {result.text}"
        assert result.cited_sources == ()
        assert ABSTENTION_MESSAGE.lower() in result.text.lower()