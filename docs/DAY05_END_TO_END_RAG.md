# Day 5: End-to-End RAG, Citations & Calibrated Abstention

**Focus:** Connecting semantic vector retrieval to the generative LLM, requiring grounded citations, handling conflicting or insufficient evidence, and understanding why cosine similarity is not calibrated probability.

---

## 🌟 The Most Important Concept: Retrieval Provenance vs Calibrated Groundedness
In naive RAG tutorials, people assume:
$$\text{Cosine Similarity} = 0.82 \implies 82\%\text{ Probability the answer is correct}$$

**This is false.**
- **Cosine similarity** only measures the geometric alignment between the query vector and document chunk vectors.
- A document chunk might have high similarity because it shares semantic themes with the question, yet still **completely fail to answer the specific question asked**, or worse, contain outdated/contradictory facts.
- **Context provenance (retrieval IDs)** proves only *what was shown* to the model—not that the model's generated claim is factually supported by that text.

```
[ User Query ] ──► [ Vector Search (Qdrant) ]
                            │
               Top-k Chunks (Similarity Score: 0.78)
                            │
                            ▼
[ LLM Generation Prompt ]
  - Must explicitly demand: "Cite [POL-XXX] for every claim"
  - Must instruct: "If the context doesn't explicitly answer, ABSTAIN"
                            │
                            ▼
[ Grounded Answer with Verifiable Citations OR Explicit Abstention ]
```

---

## 🔑 Key Takeaways & Design Patterns

### 1. The Strict Abstention Contract
If the retriever returns zero documents above the similarity threshold, or if the retrieved documents do not contain the answer:
- The system must return a predictable fallback:
  > *"I cannot answer from the available policies. Please contact support."*
- **Golden rule:** In banking and finance, an abstention is a **successful, safe response**; an invented answer is a **critical failure**.

### 2. Citation Extraction & Verification
- Rather than blindly accepting that the model cited the right document, our service verifies that every citation in the text (e.g. `[POL-001]`) matches an actual document ID present in the retrieved context set.

### 3. Chunking Tradeoffs (Small vs Large Chunks)
| Strategy | Pros | Cons |
|---|---|---|
| **Small Chunks (e.g. 100-200 tokens)** | Higher embedding precision; lower chance of diluting key facts with irrelevant text. | Loses surrounding context; sentence fragments may lack subject/antecedent. |
| **Large Chunks (e.g. 500-1000 tokens)** | Preserves full semantic context and relationships. | Averages out fine-grained facts; consumes more context window tokens. |

For policy documents, **clause-level chunking with metadata** (`id`, `category`, `version`) provides the optimal balance.

---

## 🛠️ Artifacts & Code Delivered
- `bankassist/rag.py`: End-to-end RAG orchestrator integrating `QdrantVectorRetriever` with `Generator`, verifying citation provenance and enforcing abstention.
- `tests/test_rag.py`: 5 supported and 5 unsupported test cases comparing retrieval behavior.

---

## 🎯 Interview Check-in
> **Q: Why is a high cosine similarity score not a guarantee of answer correctness?**  
> *A:* Cosine similarity measures directional alignment in embedding space, not logical entailment or factual veracity. A query and a document can be highly similar topical matches while having conflicting premises or omitting the exact detail requested. Ensuring correctness requires strict prompt abstention rules, citation verification, and offline evaluation harnesses.

