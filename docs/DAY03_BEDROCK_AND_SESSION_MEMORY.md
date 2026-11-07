# Day 3: Bedrock Inference, Tokens, Prompts & Session Memory

**Focus:** Interfacing with LLMs reliably, managing context windows via bounded session memory, versioning system prompts, and collecting telemetry.

---

## 🌟 The Most Important Concept: The Context Window & Bounded Session Memory
An LLM has no memory between API calls. Conversation history must be explicitly passed into each request. 

However, appending conversation history indefinitely creates two critical production failures:
1. **Context Window Exhaustion:** Hard API errors when total tokens exceed the model's limit.
2. **Quadratic Cost & Latency Growth:** Every turn re-processes all previous turns.

```
Turn 1: [User]                              -> 20 tokens in
Turn 2: [Turn 1 History] + [User]           -> 80 tokens in
Turn 5: [Turns 1-4 History] + [User]        -> 350 tokens in
...
Solution: Bounded Sliding Window (Keep only last N turns)
[Turn N-3, Turn N-2, Turn N-1] + [Current User Prompt] -> Fixed Upper Bound!
```

---

## 🔑 Key Takeaways & Design Patterns

### 1. Unified Inference via AWS Bedrock `Converse` API
- Older Bedrock `InvokeModel` required unique JSON request/response formats for each model vendor (Anthropic vs Amazon vs Meta).
- The `Converse` API provides a standardized multi-turn message interface (`messages`, `system`, `inferenceConfig`) across all Bedrock foundation models.

### 2. Deterministic Inference via Temperature 0.0
- For creative text, higher temperatures (`0.7`–`1.0`) allow sampling across lower-probability tokens.
- For banking and policy Q&A, **`temperature = 0.0`** (greedy decoding) is essential to maximize repeatability, minimize hallucinations, and ensure strict citation adherence.

### 3. System Prompt as Versioned Code (`PROMPT_VERSION = "v1.0.0"`)
- Prompts dictate system behavior just like source code.
- Always version prompts in code and emit `prompt_version` in response telemetry so that regressions can be linked to exact prompt edits.

### 4. Telemetry as a First-Class Output
- Every inference response tracks:
  - `model_id` (e.g. `amazon.nova-micro-v1:0`)
  - `prompt_version` (e.g. `v1.0.0`)
  - `input_tokens` and `output_tokens` (for precise cost attribution)
  - `latency_ms` (to enforce SLA budgets)

---

## 🛠️ Artifacts & Code Delivered
- `bankassist/session.py`: `SessionStore` protocol and `InMemorySessionStore` with sliding window memory (`max_turns`).
- `bankassist/generator.py`: Versioned system prompt, `BedrockGenerator` (with request timeouts), and `MockLLMGenerator` for deterministic offline testing.
- `bankassist/core.py`: Updated `BankAssistant` orchestrating bounded history and telemetry.
- `tests/test_session_and_telemetry.py`: Unit tests validating bounded memory and telemetry metrics.

---

## 🎯 Interview Check-in
> **Q: How do you prevent conversation history from overflowing your context window and blowing up your API budget?**  
> *A:* Enforce a bounded conversation memory strategy (such as a sliding window retaining the last $N$ turns or an LLM-based summary buffer) at the application session layer before formatting the prompt for the model.

