# Day 1: BankAssist Scope, Architecture, and Risk Plan

**Author / Engineer:** Hadi  
**Date:** 2026-11-06  
**Status:** In Progress (Day 1 Working Draft)

---

## 1. Product Context & Objectives
- **Product Name:** BankAssist
- **Core Mission:** An educational, secure, text-first (with voice extension) conversational banking assistant for a fictional bank.
- **Key Philosophy:** 
  - Educational simulation with strict trust boundaries.
  - No real financial accounts or transactional mutations (read-only balance/transactions for synthetic personas).
  - Grounded answers strictly from versioned bank policies; refuse/abstain when ungrounded.

---

## 2. Five User Stories with Acceptance Criteria (Given / When / Then)

### US1: Policy FAQ with Citation (FR1)
- **Story:** As a retail banking customer, I want to ask questions about bank policies (e.g. lost card, fees, address changes) so that I get accurate, sourced guidance.
- **Acceptance Criteria:**
  - *Given* a query directly covered by an approved policy (e.g., "How do I report a lost card?"),
  - *When* BankAssist responds,
  - *Then* the response provides correct instructions, cites the source document ID (e.g., `POL-001`), and explicitly notes demo limitations (e.g., cannot freeze the card).

### US2: Graceful Abstention on Unsupported Queries (FR2)
- **Story:** As a customer asking questions outside the bank's documented policies (e.g., mortgage rates, investment advice), I want the assistant to clearly state it cannot answer so that I am not misled by hallucinated financial advice.
- **Acceptance Criteria:**
  - *Given* a query not covered by the current policies (e.g., "What is the mortgage interest rate?"),
  - *When* BankAssist processes the query,
  - *Then* it abstains with a predefined escalation/support message and provides zero ungrounded facts or invented rates.

### US3: Conversational Context & Multi-Turn Clarification (FR3)
- **Story:** As a customer comparing products, I want to ask follow-up questions referencing earlier context so that I do not have to repeat the entire question.
- **Acceptance Criteria:**
  - *Given* an earlier turn asking "What is the Demo Basic monthly fee?" and a follow-up "And what about the student account?",
  - *When* BankAssist processes the follow-up,
  - *Then* it uses bounded session history to correctly resolve the reference to student account fees and returns 0 demo credits (POL-002).

### US4: Authenticated, Authorised Balance Inquiry (FR4)
- **Story:** As an authenticated customer, I want to check my account balance so that I know my current funds without risk of another customer seeing my data.
- **Acceptance Criteria:**
  - *Given* an authenticated user session (`customer_id: cust_101`),
  - *When* the user asks "What is my current balance?",
  - *Then* the server invokes the read-only `get_balance` tool bound to `cust_101` and returns their synthetic balance;
  - *And* if the prompt attempts to query `cust_102`, the server rejects the request at the tool layer with an authorization error before any data lookup occurs.

### US5: Voice Interaction Round-Trip (FR5)
- **Story:** As a user on mobile or hands-free, I want to speak my question and hear the answer so that I can interact without typing.
- **Acceptance Criteria:**
  - *Given* an audio recording of a supported policy question,
  - *When* sent to the voice endpoint,
  - *Then* the audio is transcribed via Amazon Transcribe, routed through the standard BankAssist pipeline, and the reply is synthesized via Amazon Polly accompanied by text transcript, without reading out sensitive PII/secrets.

---

## 3. Prioritized & Estimated Backlog

| Priority | Item | Estimate | Primary Risk / Dependency |
|---|---|---|---|
| **P0** | Typed FastAPI `/chat` endpoint & Pydantic models | 1.5h | Clean error handling; strictly no SDK logic in routes |
| **P0** | Bedrock Generator & bounded session history | 2.0h | Bedrock credentials, latency, context window trimming |
| **P0** | Vector DB indexing (local Qdrant) & embeddings | 3.0h | Chunking strategy, embedding dimension consistency |
| **P0** | RAG with verifiable citations & abstention logic | 2.0h | Hallucinations; tuning similarity threshold vs abstention |
| **P1** | Evaluation harness (40 cases, deterministic + rubric) | 3.0h | Overfitting to dev set; test leakage |
| **P1** | Security guardrails & authorization boundaries | 3.0h | Prompt injection, cross-user data leakage |
| **P1** | Synthetic read-only tool execution (`get_balance`) | 2.0h | Tool-loop limits; keeping identity server-enforced |
| **P2** | Voice pipeline (Transcribe + Polly integration) | 1.5h | Latency budget, transcription errors on noisy audio |
| **P2** | Terraform infrastructure definition (S3, IAM, CloudWatch) | 3.0h | IAM least-privilege scoping, cost guardrails |
| **P2** | Telemetry, structured logs, and rollback runbook | 2.0h | PII redaction in logs; version traceability |
| **P3** | SageMaker JumpStart fine-tuning design (paper/design) | 1.5h | Cloud costs / GPU quota constraints |

---

## 4. Trust Boundaries & Architecture Sketch

```
[ Client / Browser / Mobile ]
           │
  (HTTPS / JWT Bearer Token)  ───► [ TRUST BOUNDARY 1: Authentication ]
           ▼
[ FastAPI Service Gateway ]
   - Validates JWT & extracts customer_id (e.g., cust_101)
   - Enforces rate limits & input size validation
   - Redacts PII before logging
           │
           ├───► [ Bedrock Guardrails ] (Input filter: toxic, jailbreak, sensitive PII)
           │
           ├───► [ Vector DB (Qdrant) ] (Policy search: read-only public bank rules)
           │            │
           │            ▼ (Retrieved policy chunks + Provenance IDs)
           │
           ├───► [ Bedrock LLM (Converse API) ]
           │       - System prompt defines role & tone
           │       - Bounded conversation history
           │       - UNTRUSTED: LLM output is treated as untrusted draft!
           │            │
           │            ▼ (Optional tool call request: "get_balance")
           │
           └───► [ TRUST BOUNDARY 2: Server-Side Tool Execution ]
                   - Tool Runner enforces: customer_id comes from JWT, NOT LLM text!
                   - Read-only data store for synthetic accounts
                   - Returns structured tool output back to LLM
           │
           ▼
[ Output Guardrails & Schema Validator ]
   - Verify citation format & sanitize response
   - Output to client (Text or Polly speech)
```

### Key Principles of the Boundary:
1. **The LLM is NOT an authorization engine.** It cannot be trusted to verify who the caller is.
2. **Context provenance != groundedness proof.** Just because an ID is attached doesn't mean the LLM didn't hallucinate. Output checks and abstention logic are required.
3. **Retrieval data is untrusted input.** Documents could contain indirect prompt injection; system prompts isolate context in clear XML/delimiters.

---

## 5. Platform Choices & Budget Guardrails

- **AWS Region:** `us-east-1` (or `eu-west-1` / `us-west-2` based on model availability).
- **LLM Model for Converse API:** `anthropic.claude-3-haiku-20240307-v1:0` or `amazon.nova-micro-v1:0` (Fast, highly cost-effective for conversational FAQ and tool calling).
- **Embedding Model:** `amazon.titan-embed-text-v2:0` (high quality, low cost, 1024 or 512 dimensions).
- **Vector Store:** Local Qdrant instance (in-memory or Docker container) for zero-cost local dev.
- **Budget & Guardrail:**
  - Maximum 2-week spend limit: **$10.00 USD**.
  - Setup AWS CloudWatch billing alert at **$5.00** threshold.
  - Disable any model or endpoint not in active use.

---

## 6. Risk Register (Top Risks & Mitigations)

| ID | Risk Description | Severity | Mitigation Strategy |
|---|---|---|---|
| **R1** | **Direct & Indirect Prompt Injection:** Attacker injects instructions via chat or documents to override guardrails. | High | Delimiters in prompts; Bedrock Guardrails; hard tool-level constraints; read-only data. |
| **R2** | **Cross-User Data Leakage (IDOR):** Attacker asks for another user's balance or account history. | Critical | Server binds `customer_id` from auth context (JWT/session), ignoring any account number in the prompt. |
| **R3** | **Hallucinated Financial Advice / Policies:** Model invents interest rates or fees when policies are missing. | High | Strict abstention instructions; temperature 0.0; similarity cutoff thresholds; deterministic evaluation suite. |
| **R4** | **PII & Secrets Logging:** Real or synthetic sensitive data (names, balances, keys) leak into CloudWatch logs. | Medium | PII scrubbing middleware on all request/response loggers; use environment variables / Secrets Manager. |
| **R5** | **Cloud Cost Overrun / Runaway Loops:** Unbounded tool calling loops or multi-turn chats exhausting API budget. | Medium | Max tool iterations capped at 2; request timeouts (5s); AWS budget alerts. |

---

## 7. Ownership & Governance Matrix

| Domain | Responsible Role | Key Decision & Artifact |
|---|---|---|
| **Requirements** | Product Owner (PO) | Defines user stories, acceptance criteria, and policy scope (`PROJECT_BRIEF.md`). |
| **Platform Design** | AI / Systems Architect | Defines trust boundaries, model/vector DB selection, latency budgets, and security posture. |
| **Quality & Eval** | QA / AI Test Engineer | Owns the 40-case evaluation harness, ground truth labels, deterministic checks, and human rubric. |
| **Release Decisions** | Joint (PO + Lead Eng + Security) | Release sign-off based on CI pass rate, evaluation benchmark thresholds (hit@3 > 90%, 0 leaks), and security verification. |

