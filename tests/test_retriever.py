import json
from pathlib import Path
from bankassist.core import Document
from bankassist.retriever import QdrantVectorRetriever, SimpleHashEmbedder


def load_policies() -> list[Document]:
    path = Path(__file__).resolve().parent.parent / "data" / "policies.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Document(id=d["id"], text=d["text"]) for d in data]


def test_qdrant_retriever_10_cases():
    docs = load_policies()
    embedder = SimpleHashEmbedder(dim=256)
    retriever = QdrantVectorRetriever(embedder=embedder, location=":memory:", score_threshold=0.1)
    retriever.index_documents(docs)

    test_queries = [
        ("How do I report a lost card?", "POL-001"),
        ("What is the basic account monthly fee?", "POL-002"),
        ("How to dispute a charge on my statement?", "POL-003"),
        ("How do I change my address?", "POL-004"),
        ("When do domestic wire transfers process?", "POL-005"),
        ("How does overdraft protection work?", "POL-006"),
        ("How long does card replacement take?", "POL-007"),
        ("Do I need a travel notice before using my card abroad?", "POL-008"),
        ("What is the minimum balance for high-yield savings?", "POL-009"),
        ("How many free transactions with business checking?", "POL-010"),
    ]

    for query, expected_id in test_queries:
        retrieved = retriever.retrieve(query, top_k=2)
        retrieved_ids = [d.id for d in retrieved]
        assert expected_id in retrieved_ids, f"Query '{query}' failed to retrieve {expected_id}. Got: {retrieved_ids}"


def test_qdrant_abstains_on_unrelated_query():
    docs = load_policies()
    embedder = SimpleHashEmbedder(dim=256)
    retriever = QdrantVectorRetriever(embedder=embedder, location=":memory:", score_threshold=0.4)
    retriever.index_documents(docs)

    # Completely alien query with no financial or bank keywords
    unrelated = "What is the boiling point of liquid nitrogen in outer space?"
    retrieved = retriever.retrieve(unrelated, top_k=2)
    assert len(retrieved) == 0, f"Expected 0 results for unrelated query, got: {[d.id for d in retrieved]}"