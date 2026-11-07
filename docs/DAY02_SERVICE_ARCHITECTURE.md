# Day 2: Service Architecture, API Contracts & Dependency Injection

**Focus:** Transforming an offline script into a clean, testable service with strict typing and swappable components.

---

## 🌟 The Most Important Concept: Dependency Injection (DI) & Decoupling
In real-world GenAI engineering, **never import or call LLM or vector-store provider SDKs directly inside API route handlers or core business logic**.

```
[ HTTP Route (/chat) ]
         │ (calls)
         ▼
[ Service Boundary: BankAssistant ]
         │ (depends only on Protocols)
         ├──► Retriever Protocol  ──► [ KeywordRetriever / QdrantVectorRetriever / FakeRetriever ]
         └──► Generator Protocol  ──► [ ExtractiveGenerator / BedrockGenerator / FakeGenerator ]
```

### Why this matters:
1. **Zero-cost, millisecond test runs:** Fast unit testing without spending cloud credits or calling AWS Bedrock APIs.
2. **Provider Agnostic:** Switching from Bedrock to Azure OpenAI, Anthropic, or an open-weight model on vLLM requires zero changes to the API endpoint or service layer.
3. **Deterministic Error Handling:** The API layer translates domain exceptions into standard HTTP error responses.

---

## 🔑 Key Takeaways & Design Patterns

### 1. Pydantic Request & Response Boundaries (`bankassist/schemas.py`)
- Always validate incoming payload constraints (`min_length`, `max_length`, structure) before any inference or retrieval pipeline is triggered.
- Protects downstream components from malformed or malicious inputs.

### 2. Python `typing.Protocol` for Duck Typing
- Interfaces in Python are defined with `typing.Protocol`.
- Classes don't need to inherit explicitly from an abstract base class; as long as they implement the expected method signatures (e.g. `retrieve(question)` or `generate(question, docs)`), Python and type checkers treat them as valid implementations.

### 3. FastAPI Dependency Overrides in Tests
- Using `app.dependency_overrides[get_assistant] = lambda: fake_assistant` allows unit and integration tests to substitute test doubles on the fly without patching global modules.

---

## 🛠️ Artifacts & Code Delivered
- `bankassist/schemas.py`: `ChatRequest` and `ChatResponse` models.
- `bankassist/core.py`: `Retriever` and `Generator` Protocols, `BankAssistant` orchestrator.
- `bankassist/api.py`: FastAPI `/chat` endpoint using FastAPI's dependency injection (`Depends`).
- `tests/test_api.py`: End-to-end endpoint tests for valid queries, unsupported questions, and empty payloads.

---

## 🎯 Interview Check-in
> **Q: Why should an AI engineer avoid instantiating Bedrock or OpenAI clients directly in an API route?**  
> *A:* Doing so tightly couples the transport layer to third-party SDKs, breaks unit testability without complex mocking, leaks credentials into request handlers, and makes it impossible to substitute local or offline adapters for offline testing and deterministic CI runs.

