# BankAssist project brief

## Product goal

Help a fictional bank customer understand policies and inspect synthetic account information through a text-first conversational assistant, with a short voice demonstration.

## Functional requirements

FR1: Answer from versioned approved policy documents and provide supporting citations.
FR2: Abstain and offer support escalation when evidence is insufficient or conflicting.
FR3: Resolve follow-up questions using bounded, isolated session history.
FR4: Retrieve a balance or recent transactions only for the authenticated synthetic customer.
FR5: Accept a short voice recording and return synthesized speech plus text.
FR6: Capture optional user feedback without retaining unnecessary personal data.

No transfers, lending decisions, card changes or real bank integration. All money values and policies are synthetic. Support escalation is a displayed next step unless a real handoff integration is explicitly implemented.

## Non-functional requirements

- Authentication and authorization at the service/tool/retrieval layers; never infer identity from chat text.
- Encryption in transit and at rest in a cloud deployment; least-privilege roles and managed secrets.
- Request timeouts, bounded retries, input/output limits, tool-loop limit and predictable fallback.
- Session isolation, redacted observability, declared retention and deletion behavior.
- Reproducible configuration, tests, versioned releases and documented rollback.
- Measurable answer quality, latency and cost; see the evaluation contract in the plan.
- Threat model includes user injection, malicious documents, cross-tenant retrieval, tool misuse, logging leaks and dependency risks.

## Target request path

Text or audio enters an authenticated API. Audio is transcribed. Application code establishes identity and session scope. Input checks run before routing. The assistant retrieves authorized policy chunks or requests an allowlisted read-only tool. Tool code validates identity and arguments independently. The model drafts a response from approved evidence/tool output. Output checks run before text or synthesized speech is returned. Redacted telemetry records versions and outcomes.

Guardrails reduce selected risks but do not establish customer authorization, guarantee truth, or replace application controls. Treat retrieved documents and tool output as untrusted data, not instructions.

## Backlog with rough implementation estimates

These estimates are practice inputs, not commitments; compare actuals daily. They fit inside the plan's build blocks only if scope stays small.

| Item | Initial estimate | Acceptance criterion |
| --- | --- | --- |
| Typed chat endpoint | 1.5 hours | Valid request works; malformed/empty input rejected |
| Bedrock generator and history | 2 hours | Two-turn interaction; timeouts handled |
| Embedding index and retrieval | 3 hours | Expected source retrieved on labeled examples |
| RAG with citations and abstention | 2 hours | Unsupported request does not invent a policy |
| Evaluation runner and rubric | 3 hours | Versioned per-case report with failures |
| Guardrails and access boundaries | 3 hours | Tested malicious input and cross-user access |
| Read-only agent tools | 2 hours | Typed tool calls; failure never reported as success |
| Voice round trip | 1.5 hours | Five synthetic recordings tested |
| Terraform and delivery pipeline | 3 hours | Validated plan and test-blocked release |
| SageMaker experiment design | 1.5 hours | Dataset splits, baseline, cost and cleanup defined |
| Telemetry and rollback | 2 hours | Reproduce failure and revert release |

## Collaboration practice

On day 1, write a product-owner brief: customer need, scope, acceptance and assumptions. Write an architect note: service/data boundaries and deployment tradeoffs. Write a developer note: API contracts and dependencies. If studying alone, role-play these reviews; if a peer is available, request feedback. At day 7, demonstrate failures and adjust estimates. At day 14, present evidence and propose the next sprint.

## Five-minute final demo

1. Ask a fictional policy question and inspect its citation.
2. Ask an unsupported question and demonstrate abstention.
3. Ask for your synthetic balance; then attempt another customer's balance.
4. Show an injection test and a failed-tool fallback.
5. Run one voice example and show quality/latency metrics plus release versions.

## Portfolio claims

Only say 'deployed', 'fine-tuned', 'integrated' or 'measured' when you actually performed the action and retained evidence. Otherwise label the item as a design, stub, experiment plan or future work. The supplied baseline is tested locally; it is not a finished GenAI system.
