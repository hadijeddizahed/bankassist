# Day 4: Embeddings, Vector Search & Qdrant Indexing

**Focus:** Moving from brittle keyword matching to semantic vector retrieval with local vector database indexing and score thresholding.

---

## 🌟 The Most Important Concept: Semantic Vector Search vs Keyword Matching
Keyword search (lexical matching) looks for exact word overlap. If a user asks *"How do I report a misplaced card?"* and the policy says *"Report a lost or stolen card"*, keyword search scores low or fails completely.

Vector embeddings map words and sentences into a high-dimensional geometric space where **semantic meaning** is encoded as spatial direction:

```
"lost card"      ──[ Embedding Model ]──►  [ 0.12, -0.45,  0.88, ... ] (Vector A)
"stolen plastic" ──[ Embedding Model ]──►  [ 0.14, -0.43,  0.86, ... ] (Vector B)
                     
                     Cosine Similarity ≈ 0.94 (Near Identical Angle!)
```

---

## 🔑 Key Takeaways & Design Patterns

### 1. Embeddings vs Generation: Different Models, Different Roles
| Attribute | Embedding Model (e.g. Titan Text Embeddings v2) | Generation Model (e.g. Nova Micro, Claude) |
|---|---|---|
| **Architecture** | Bi-directional Encoder | Auto-regressive Decoder |
| **Output** | Fixed-dimension float vector (e.g. 512 numbers) | Variable-length token sequence (text) |
| **Primary Math** | Vector geometry / Dot product / Cosine distance | Next-token probability distribution |
| **Interface** | `embed_text(str) -> list[float]` | `generate(messages) -> str` |

### 2. Cosine Similarity & Normalization
- Cosine similarity measures the cosine of the angle between two vectors:
  $$\text{Cosine Similarity} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$
- When vectors are normalized to unit length ($\|\mathbf{u}\| = 1$), cosine similarity simplifies to a fast dot product: $\mathbf{u} \cdot \mathbf{v}$.

### 3. Score Thresholding for Rejection / Abstention
- In banking, retrieving an irrelevant document because it was the "least bad" match causes hallucinations.
- By configuring a **`score_threshold`** (e.g. `0.35`), Qdrant drops results whose cosine similarity falls below the cutoff, allowing the assistant to abstain when no relevant policy exists.

### 4. Local In-Memory Vector Storage with Qdrant
- Using `QdrantClient(location=":memory:")` provides full vector indexing and filtering inside the Python process without requiring Docker containers or cloud infrastructure for tests.

---

## 🛠️ Artifacts & Code Delivered
- `data/policies.json`: Expanded fictional policy corpus (12 comprehensive policies).
- `bankassist/retriever.py`:
  - `EmbeddingFunction` protocol
  - `SimpleHashEmbedder` (fast, deterministic local embedding for offline testing)
  - `TitanEmbedder` (Bedrock Titan Text Embeddings v2 adapter)
  - `QdrantVectorRetriever` (in-memory Qdrant collection with cosine distance and score thresholds)
- `tests/test_retriever.py`: Validation suite covering 10 distinct queries and abstention on unrelated queries.

---

## 🎯 Interview Check-in
> **Q: Why are embeddings and chat generation handled by separate interfaces and models in production RAG systems?**  
> *A:* Because they solve fundamentally different problems. Embeddings compress text into a static spatial representation for index-time geometric search. Generative models synthesize, reason, and draft language from retrieved evidence. Combining them into one interface would violate the single-responsibility principle and prevent independent scaling, caching, and model selection.

