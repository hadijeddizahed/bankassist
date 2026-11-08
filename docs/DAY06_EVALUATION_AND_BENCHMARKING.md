# Day 6: Evaluation Frameworks, Hallucinations & Test Leakage

**Focus:** Moving from ad-hoc unit tests to systematic offline evaluation: building a 40-case evaluation suite, separating development from held-out splits, deterministic checks, and human scoring rubrics.

---

## 🌟 The Most Important Concept: Test Set Leakage & Offline Evaluation Contract
In traditional software, if unit tests pass, you ship. In Generative AI, passing 5 prompt tests in your terminal means almost nothing because:
1. **LLM stochasticity:** A small prompt tweak that fixes one question can silently break 10 other questions.
2. **Test Leakage (Data Contamination):** If you build your prompt, similarity threshold, and chunking while continuously testing on the exact same 10 questions, you are **overfitting**. The system looks perfect to you, but fails on real customer queries.

```
                    [ 40 Distinct Evaluation Cases ]
                                   │
                 ┌─────────────────┴─────────────────┐
                 ▼                                   ▼
       [ Development Split (25) ]           [ Held-out Split (15) ]
       - Used daily to tune prompts         - NEVER touched during daily tuning!
       - Used to set similarity thresholds  - Run only before releases to measure
       - Failure analysis & debugging         true generalization.
```

---

## 🔑 Key Takeaways & Design Patterns

### 1. The 40-Case Evaluation Split (Contract)
From [TWO_WEEK_PLAN.md](file:///Users/hadi/PycharmProjects/bankassist/TWO_WEEK_PLAN.md#L33):
- **15 Supported policy questions:** Must retrieve correct documents and cite them.
- **5 Unsupported questions:** Must abstain cleanly with zero fabricated facts.
- **5 Multi-turn conversations:** Must contextualize follow-ups and resolve pronouns.
- **5 Tool/Authorization cases:** Cross-user checks and balance inquiries (Days 7-8).
- **5 Injection / Adversarial cases:** Jailbreak and prompt injection attempts (Day 7).
- **5 Voice utterances:** Synthetic noisy speech tests (Day 9).

### 2. The Evaluation Metrics
| Metric | Target | How it is computed |
|---|---|---|
| **Retrieval Hit@3** | $\ge 90\%$ | Did the top 3 retrieved documents contain at least one expected ground truth source ID? |
| **Answer Groundedness** | $\ge 90\%$ | Are factual claims supported by the cited policy text (human rubric / deterministic check)? |
| **Abstention Rate** | $\ge 90\%$ | Did unsupported questions output the official support escalation text without hallucinating? |
| **Citation Correctness** | $100\%$ | Did cited `[POL-XXX]` tags exist in the retrieved context set (no ghost citations)? |

### 3. Evaluation Triad: Deterministic Checks vs Human Rubric vs LLM-as-a-Judge
- **Deterministic Checks (Code):** Verify schema, JSON format, presence of citations, abstention phrasing, and security invariants (100% reproducible, 0 cost).
- **Human Rubric:** Golden standard for factual entailment and helpful tone on held-out samples.
- **LLM-as-a-Judge:** Scalable automated grading (e.g. Claude 3 evaluating Nova's responses) that must be periodically calibrated against human labels. Never use an LLM judge as the sole release gate.

---

## 🛠️ Artifacts & Code Delivered
- `data/evaluation_full.jsonl`: 40 distinct test specifications divided into `dev` (25) and `held_out` (15).
- `bankassist/evaluator.py`: Automated evaluation runner computing Hit@3, Groundedness, Abstention, Latency, and generating a versioned evaluation report.
- `tests/test_evaluation_runner.py`: Verification that the evaluation suite runs and generates valid metrics.

---

## 🎯 Interview Check-in
> **Q: How do you prevent test leakage when evaluating an AI assistant, and how do you calibrate an LLM-as-a-judge?**  
> *A:* Split evaluation datasets into a development set (used for iterative prompt/retrieval tuning) and a strictly held-out test set run only as a release gate. To calibrate an LLM judge, score a sample with human reviewers using a fixed rubric, measure Cohen's kappa or agreement percentage with the LLM judge, and refine the judge's prompt until it aligns with human consensus.

