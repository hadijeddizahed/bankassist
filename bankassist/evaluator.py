from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from bankassist.rag import RAGPipeline


@dataclass
class CaseResult:
    case_id: str
    split: str
    category: str
    question: str
    expected_sources: list[str]
    retrieved_sources: list[str]
    cited_sources: list[str]
    actual_answer: str
    is_abstention: bool
    retrieval_hit: bool
    citation_correct: bool
    passed: bool
    notes: str = ""


@dataclass
class EvaluationSummary:
    total_cases: int = 0
    passed_cases: int = 0
    retrieval_hits: int = 0
    abstention_successes: int = 0
    citation_successes: int = 0
    case_results: list[CaseResult] = field(default_factory=list)

    @property
    def hit_at_3_rate(self) -> float:
        supported_cases = [c for c in self.case_results if c.expected_sources]
        if not supported_cases:
            return 1.0
        return sum(1 for c in supported_cases if c.retrieval_hit) / len(supported_cases)

    @property
    def pass_rate(self) -> float:
        if not self.total_cases:
            return 0.0
        return self.passed_cases / self.total_cases


class EvaluationRunner:
    """Automated benchmark runner for offline RAG evaluation."""

    def __init__(self, pipeline: RAGPipeline):
        self.pipeline = pipeline

    @staticmethod
    def load_dataset(dataset_path: Path | None = None, split: str = "dev") -> list[dict[str, Any]]:
        path = dataset_path or Path(__file__).resolve().parent.parent / "data" / "evaluation_full.jsonl"
        cases = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line.strip())
                    if split == "all" or item.get("split") == split:
                        cases.append(item)
        return cases

    def evaluate_split(self, split: str = "dev") -> EvaluationSummary:
        cases = self.load_dataset(split=split)
        summary = EvaluationSummary(total_cases=len(cases))

        for item in cases:
            case_id = item["id"]
            question = item["question"]
            expected = item.get("expected_sources", [])
            category = item.get("category", "general")
            history_data = item.get("history", [])

            session_id = f"eval_{case_id}"
            if self.pipeline.session_store and history_data:
                self.pipeline.session_store.clear(session_id)
                for h in history_data:
                    self.pipeline.session_store.add_message(session_id, h["role"], h["text"])

            result = self.pipeline.run(question, session_id=session_id)

            # Check retrieval hit@3
            retrieval_hit = True
            if expected:
                retrieval_hit = any(src in result.retrieved_sources[:3] for src in expected)

            # Check citation correctness (no ghost citations)
            citation_correct = all(c in result.retrieved_sources for c in result.cited_sources)

            # Check outcome
            if category == "unsupported":
                passed = result.is_abstention
                notes = "Correctly abstained" if passed else "FAILED: Did not abstain"
                if passed:
                    summary.abstention_successes += 1
            elif expected:
                passed = retrieval_hit and not result.is_abstention and bool(result.cited_sources)
                notes = "Correctly cited" if passed else "FAILED: Missing expected source or citation"
            else:
                # Tools and security cases handled on Days 7-8
                passed = True
                notes = "Informational test"

            if retrieval_hit:
                summary.retrieval_hits += 1
            if citation_correct:
                summary.citation_successes += 1
            if passed:
                summary.passed_cases += 1

            summary.case_results.append(
                CaseResult(
                    case_id=case_id,
                    split=item.get("split", split),
                    category=category,
                    question=question,
                    expected_sources=expected,
                    retrieved_sources=list(result.retrieved_sources),
                    cited_sources=list(result.cited_sources),
                    actual_answer=result.text,
                    is_abstention=result.is_abstention,
                    retrieval_hit=retrieval_hit,
                    citation_correct=citation_correct,
                    passed=passed,
                    notes=notes,
                )
            )

        return summary