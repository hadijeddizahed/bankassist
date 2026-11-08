import configparser
import os
import time
from dataclasses import dataclass
from typing import Any
from bankassist.core import Document
from bankassist.session import Message


PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = f"""You are BankAssist, a helpful and strictly factual fictional banking assistant.
System Prompt Version: {PROMPT_VERSION}
Rules:
1. Answer the user's question ONLY using the provided Policy Documents below.
2. If the policy documents do not contain the answer, say exactly:
   "I cannot answer from the available policies. Please contact support."
3. Do NOT make up rules, interest rates, fees, or policy details.
4. Always cite the document ID (e.g. [POL-001]) for any factual statement you make.
5. This is a fictional educational demo. Never claim to freeze real cards or move real money.
"""


@dataclass
class GenerationResult:
    text: str
    prompt_version: str
    model_id: str
    output_tokens: int
    input_tokens: int
    latency_ms: int

class BedrockGenerator:
    """Real AWS Bedrock Converse API generator with timeout and token tracking."""
    def __init__(
        self,
        model_id: str = "amazon.nova-micro-v1:0",
        region_name: str | None = None,
        timeout_seconds: float = 5.0,
    ):
        import boto3
        from botocore.config import Config

        self.model_id = model_id
        region = region_name or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        config = Config(
            connect_timeout=timeout_seconds,
            read_timeout=timeout_seconds,
            retries={"max_attempts": 1},
        )
        self.client = boto3.client("bedrock-runtime", region_name=region, config=config)

    def generate(
            self,
            question: str,
            documents: list[Document],
            history: list[Message] | None = None,
    )-> GenerationResult:
        doc_context = "\n\n".join(
            f"Document ID: {doc.id}\nContent: {doc.text}" for doc in documents
        )
        user_message_with_context = (
            f"Policy Documents:\n{doc_context}\n\nUser Question: {question}"
        )
        messages: list[dict[str, Any]] = []
        if history:
            for msg in history:
                messages.append({
                    "role": msg.role,
                    "content": [{"text": msg.text}],
                })
        messages.append({
            "role": "user",
            "content": [{"text": user_message_with_context}],
        })

        start_time = time.perf_counter()
        response = self.client.converse(
            modelId=self.model_id,
            messages=messages,
            system=[{"text": SYSTEM_PROMPT}],
            inferenceConfig={
                "temperature": 0.0,
                "maxTokens": 500,
            },
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        output_text = response["output"]["message"]["content"][0]["text"]
        usage = response.get("usage", {})
        return GenerationResult(
            text=output_text,
            prompt_version=PROMPT_VERSION,
            model_id=self.model_id,
            input_tokens=usage.get("inputTokens", 0),
            output_tokens=usage.get("outputTokens", 0),
            latency_ms=round(latency_ms, 2),
        )

class MockLLMGenerator:
    """Offline deterministic mock that simulates Bedrock latency and token telemetry."""

    def __init__(self, model_id: str = "mock-model-v1"):
        self.model_id = model_id

    def generate(
            self,
            question: str,
            documents: list[Document],
            history: list[Message] | None = None,
    ) -> GenerationResult:
        if not documents:
            text = "I cannot answer from the available policies. Please contact support."
        else:
            q_lower = question.lower()
            unsupported_topics = ["mortgage", "bitcoin", "crypto", "tokyo", "weather", "car loan"]
            if any(topic in q_lower for topic in unsupported_topics):
                text = "I cannot answer from the available policies. Please contact support."
            else:
                doc_citations = ", ".join(f"[{d.id}]" for d in documents)
                text = f"According to {doc_citations}: {documents[0].text}"
        return GenerationResult(
            text=text,
            prompt_version=PROMPT_VERSION,
            model_id=self.model_id,
            input_tokens=len(question.split()) * 2 + 50,
            output_tokens=len(text.split()) * 2,
            latency_ms=12.5,
        )

