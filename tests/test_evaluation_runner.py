from pathlib import Path
from bankassist.core import Document
from bankassist.evaluator import EvaluationRunner
from bankassist.generator import MockLLMGenerator
from bankassist.rag import RAGPipeline
from bankassist.retriever import QdrantVectorRetriever, SimpleHashEmbedder
from bankassist.session import InMemorySessionStore
import json


def create_eval_pipeline() -> RAGPipeline:
    policies_path = Path(__file__).resolve().parent.parent / "data" / "policies.json"
    with open(policies_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    docs = [Document(id=d["id"], text=d["text"]) for d in data]

    embedder = SimpleHashEmbedder(dim=1024)
    retriever = QdrantVectorRetriever(
        embedder=embedder,
        location=":memory:",
        score_threshold=0.0,
    )
    retriever.index_documents(docs)
    generator = MockLLMGenerator(model_id="eval-mock-v1")
    session_store = InMemorySessionStore(max_turns=6)
    return RAGPipeline(
        retriever=retriever,
        generator=generator,
        session_store=session_store,
    )


def test_dev_evaluation_suite():
    pipeline = create_eval_pipeline()
    runner = EvaluationRunner(pipeline)

    summary = runner.evaluate_split(split="dev")

    assert summary.total_cases == 25
    # Verification of Day 6 learning target: Hit@3 >= 90%
    assert summary.hit_at_3_rate >= 0.90, f"Hit@3 was {summary.hit_at_3_rate:.2%}, expected >= 90%"
    # Verification of citation correctness
    assert summary.citation_successes == summary.total_cases