# Two-week AI Engineer preparation plan

## Goal and working rhythm

Assumptions: you know Python basics and have some software experience; you can invest 3 focused hours each day. Day numbers are relative so you can start whenever you want. If you already know a topic, demonstrate its exit check and spend the saved time on evaluation and failure analysis.

Daily rhythm: 35 minutes reading, 110 minutes building, 25 minutes testing/evaluating, 10 minutes explaining the result in your notes. Keep a small backlog with estimates and acceptance criteria. Two weeks covers every topic in the job description at introductory or applied depth; it does not replace production experience.

## Week 1: build a reliable text assistant

| Day | Learn and discuss | Build | Exit evidence |
| --- | --- | --- | --- |
| 1 | Functional vs non-functional requirements; banking use cases; stakeholder alignment; agile estimation. Review OOP, interfaces, composition and dependency injection. | Run the starter; write 5 user stories with acceptance criteria; rank a backlog and estimate each item. Sketch trust boundaries and choose a model/Region/budget. | One-page scope, architecture and risk list. Explain who owns requirements, platform design, quality and release decisions. |
| 2 | OOP Python in services; typing, exceptions, async I/O, API contracts, unit vs integration tests. | Add a FastAPI /chat endpoint and Pydantic validation; isolate retriever, generator, session store and tools. Add fake adapters for tests. | Valid/invalid request tests; no provider SDK code in the route; clear error response. |
| 3 | LLM tokens, context windows, temperature, latency, model selection, prompting and conversation memory. AWS IAM and Bedrock inference. | Implement a Bedrock generator using Converse with a compatible model. Version the system prompt; add bounded session history and timeouts. | A multi-turn demo, token/latency records, and explicit unsupported-question behavior. No secrets committed. |
| 4 | Embeddings, cosine similarity, chunk size/overlap, metadata and vector database indexing. | Expand to 10-15 fictional policies. Embed chunks, store them in local Qdrant, implement retrieval with document IDs and versions. | Retrieve expected evidence for 10 questions. Explain why embeddings and chat generation use different interfaces and may use different models. |
| 5 | End-to-end RAG; query rewriting, hybrid search and reranking tradeoffs; citation provenance and stale documents. | Connect retrieval to generation. Require citations, abstain when evidence is insufficient, and add document metadata filters. Compare two chunking settings. | Five supported and five unsupported cases reviewed. Explain why a similarity threshold is not a calibrated probability of correctness. |
| 6 | Hallucinations, unexpected bot behavior, retrieval vs generation failures; evaluation frameworks and test leakage. | Expand to 40 evaluation cases. Create deterministic checks, human scoring rubric and optional LLM-judge scoring. Separate development and held-out cases. | Baseline report with actual counts, failure examples and retrieval/answer metrics. Human-review judge disagreements. |
| 7 | AI security, prompt injection, sensitive data, responsible AI, fairness and safe escalation. | Integrate Bedrock Guardrails for input/output. Enforce authorization outside the LLM; filter retrieval by trusted identity. Test malicious retrieved text and cross-user requests. | Adversarial report, redacted logs and first-week review. Fix the three most consequential failures; document remaining risks. |

## Week 2: tools, voice, cloud delivery and operations

| Day | Learn and discuss | Build | Exit evidence |
| --- | --- | --- | --- |
| 8 | Agents vs workflows; tool selection, JSON schemas, tool results, loop limits and idempotency. | Implement get_balance and list_transactions against fake accounts. Bind access to authenticated server-side identity, validate arguments, limit iterations and handle failures. | Authorized request succeeds; cross-user request fails before data access. The assistant never claims a tool succeeded when it failed. Explain when a deterministic route is preferable to an agent. |
| 9 | Voice pipeline: speech recognition, synthesis, turn-taking, interruptions, noise and latency. | Add a short recorded-audio round trip using Transcribe, your text assistant and Polly. Keep text fallback; do not read unnecessary sensitive data aloud. | Test 5 synthetic utterances, including noise/ambiguity; record transcription errors and total latency. Streaming and barge-in remain design/stretch topics. |
| 10 | Cloud-native design, IAM least privilege, encryption, networking, state and Terraform lifecycle. | Write Terraform for a small API environment: S3, execution role, logs and API runtime. Document vector-store connectivity and secret handling. Run fmt, validate and review plan. | Reviewed infrastructure plan and architecture. If an AWS account/budget is available, deploy and smoke-test; otherwise explicitly record that provisioning is unverified. |
| 11 | Software testing, CI/CD, containers, dependency management and staged releases. | Add CI for lint, unit/integration tests and offline evaluation. Package the API. Add a separately triggered cloud smoke test and release gate. | A failing check blocks a change; successful checks produce a versioned artifact. Use short-lived CI credentials rather than stored cloud keys. |
| 12 | Prompt tuning vs RAG vs fine-tuning; SageMaker AI JumpStart; train/validation/test splits and overfitting. | Prepare synthetic intent or response-format data. Write a small fine-tuning experiment with baseline, budget, success criterion and cleanup. Run one supported small-model job only if quota/time/cost permit. | Compare held-out results if trained. Otherwise deliver the experiment design and state 'not executed'; do not claim hands-on training. Explain why changing bank policies belong in retrieval. |
| 13 | GenAIOps: artifact lineage, prompt/model/data versions, observability, drift, feedback, canaries and rollback. | Emit redacted structured events with latency, tokens, retrieval IDs, tool status and release versions. Add a KPI report, feedback triage loop and rollback runbook. | Trace a bad answer to its prompt/model/index versions; reproduce it; show a rollback rehearsal. Re-evaluate after a policy change. |
| 14 | Solution tradeoffs, stakeholder communication, effort estimation and incident discussion. | Run the held-out evaluation; fix critical defects; rehearse a 5-minute demo. Write a short architecture decision record, limitations and next-sprint estimates. | Portfolio README, measured evaluation report, architecture, tests/CI evidence, demo and honest gaps. Practice the interview prompts below. |

## Evaluation contract

Create 40 distinct cases: 15 supported policy questions, 5 unsupported questions, 5 multi-turn conversations, 5 authorization/tool cases, 5 injection/privacy cases and 5 voice utterances. Use 25 for development and 15 held out; keep near-duplicates in the same split. This is a small learning suite, not evidence of production safety.

Record query, prior turns, identity/role, expected evidence, expected behavior, actual answer, retrieved IDs, prompt/model/index versions, latency, token usage and reviewer notes. Never store real secrets in evaluation fixtures.

Proposed learning targets (not measured starter results):
- Retrieval hit@3: at least 90% of supported questions retrieve one acceptable source in the first three results. Separately measure recall if several sources are required.
- Answer groundedness: at least 90% of evaluated factual claims supported by cited context, using a human rubric; count supported claims / total factual claims.
- Unsupported-question abstention: at least 90%; also inspect unnecessary refusals on answerable questions.
- Citation correctness: verify the cited passage supports the associated claim, not merely that the ID exists.
- Tool task success: at least 90% for authorized scripted tasks; all tested cross-user access attempts denied by application code.
- Security: zero observed sensitive-data disclosures or unauthorized tool actions in the adversarial suite. Passing a tiny suite is not a guarantee.
- Text p95 latency: provisional target below 5 seconds over at least 100 measured text requests in a declared environment; report warm/cold behavior and concurrency. Voice has a separate end-to-end measurement.
- Cost: report model tokens and estimated cost per successful conversation using current regional pricing, plus infrastructure/training costs. Select a budget before running cloud experiments.

Use deterministic checks for schemas, permissions and tool side effects; human review for correctness and helpfulness; LLM judges for scalable scoring calibrated against human labels. Do not make a judge score the sole release gate. Capture failure counts and denominators rather than presenting percentages alone.

## Scope if time is tight

Protect the core: Python design, Bedrock inference, embeddings/RAG, citations, evaluation, guardrails, one authorized tool, CI and infrastructure design. Keep actual fine-tuning and fully deployed voice/cloud infrastructure as explicit stretch execution. Still study each topic and produce its design exercise. If you only have 1-2 hours/day, extend the schedule to 3-4 weeks rather than claiming the same hands-on coverage.

## Interview practice

1. When would you choose RAG, fine-tuning or a better prompt?
2. How do you distinguish missing retrieval evidence from a generation hallucination?
3. How do you prevent an agent from accessing another customer's account?
4. Why are guardrails insufficient for authorization and factual correctness?
5. What is in your offline evaluation set, and how do you calibrate an LLM judge?
6. How do you version and roll back a model, prompt and index together?
7. What changes when adding voice, and how do you measure the latency budget?
8. How would you estimate a new feature with engineers, architects and product owners?

## Official reading map

Read the relevant sections each day, not every page end to end. Verify supported Regions, models, versions and prices when implementing.

- Days 1-3: Python classes: https://docs.python.org/3/tutorial/classes.html ; Bedrock: https://docs.aws.amazon.com/bedrock/ ; Converse: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html
- Days 4-5: Bedrock Knowledge Bases overview: https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html ; Qdrant documentation: https://qdrant.tech/documentation/
- Days 6-7: Bedrock evaluation: https://docs.aws.amazon.com/bedrock/latest/userguide/evaluation.html ; Guardrails: https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html
- Day 8: Bedrock agents: https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html
- Day 9: Transcribe: https://docs.aws.amazon.com/transcribe/latest/dg/what-is.html ; Polly: https://docs.aws.amazon.com/polly/latest/dg/what-is.html
- Days 10-11: Terraform AWS tutorials: https://developer.hashicorp.com/terraform/tutorials/aws-get-started ; GitHub Actions: https://docs.github.com/en/actions
- Day 12: SageMaker AI JumpStart: https://docs.aws.amazon.com/sagemaker/latest/dg/jumpstart-foundation-models.html
- Day 13: CloudWatch: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html
