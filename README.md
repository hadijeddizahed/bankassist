# BankAssist: a two-week AI engineering lab

A fictional banking assistant for someone who already knows Python fundamentals.
Budget: 3 hours/day for 14 days (42 hours). Aim for a credible prototype and evidence of learning, not production banking readiness.

## Start now

Requires Python 3.10 or newer. No packages, API key, or cloud account needed for this baseline.
Run from this directory:

```bash
python -m bankassist "How do I report a lost card?"
python -m unittest discover -s tests -v
```

The starter implements object-oriented interfaces, keyword retrieval, extractive answers, four fictional policies, three tests, and six evaluation seed cases. It does NOT yet implement an LLM, embeddings, vector storage, authentication, guardrails, tools, voice, cloud deployment, or fine-tuning. Those are the learning tasks. Keyword retrieval deliberately has poor relevance; the source IDs are context provenance, not an answer-groundedness guarantee.

Read TWO_WEEK_PLAN.md first, then docs/PROJECT_BRIEF.md. There are no automatic cloud actions or paid services in this starter.

## Suggested target stack

- Python, FastAPI, Pydantic, pytest, Ruff; dependency injection through Retriever and Generator interfaces.
- Bedrock for chat and embeddings; Qdrant locally for vector storage. Compare a managed Bedrock Knowledge Bases approach in your design notes rather than implementing two complete RAG stacks.
- Bedrock Guardrails plus application authorization, tool validation and retrieval permissions.
- Read-only tools backed by synthetic accounts; server-side identity determines account access.
- Docker, Terraform; AWS S3, IAM, KMS, CloudWatch, API Gateway and Lambda for a small API deployment. A production vector-store deployment is a separate design decision; do not assume local Qdrant is cloud-accessible.
- Transcribe and Polly for a short voice round trip.
- SageMaker AI JumpStart for a bounded customization experiment.

Choose supported models in your account and Region after checking current model access, quotas, pricing, and data residency needs. Do not hard-code a model identifier copied from an old tutorial. Set budget alerts and remove experimental endpoints and infrastructure when finished.

## Folder guide

- bankassist/: runnable baseline and replaceable interfaces.
- data/policies.json: synthetic source documents.
- data/evaluation_seed.jsonl: specifications to expand; these are not passing-test claims.
- tests/: baseline behavior tests only.
- docs/PROJECT_BRIEF.md: requirements, acceptance criteria and backlog.
- TWO_WEEK_PLAN.md: daily learning and build schedule.

## First exercises

1. Run the baseline and tests.
2. Try an unrelated question containing the word 'account'; observe false-positive retrieval.
3. Add one policy and an evaluation case before changing retrieval.
4. Implement a BedrockGenerator behind Generator. Keep the offline adapter for fast unit tests.
5. Replace KeywordRetriever with embedding-based retrieval and measure changes on held-out questions.

Never use real customer records, credentials, or bank documents without authorization. This is an educational simulation and makes no compliance claim.
