import pytest
from fastapi.testclient import TestClient
from bankassist.api import app, get_assistant
from bankassist.core import BankAssistant, Document, Answer

client = TestClient(app)


class FakeRetriever:
    def retrieve(self, question: str) -> list[Document]:
        if "card" in question.lower():
            return [Document(id="POL-001", text="Report lost card in app.")]
        return []


class FakeGenerator:
    def generate(self, question: str, documents: list[Document]) -> str:
        return f"Mock reply based on {len(documents)} docs."


def test_chat_valid_query():
    # Override the dependency with fake adapters
    fake_assistant = BankAssistant(retriever=FakeRetriever(), generator=FakeGenerator())
    app.dependency_overrides[get_assistant] = lambda: fake_assistant

    response = client.post("/chat", json={"message": "How to report lost card?"})
    assert response.status_code == 200
    data = response.json()
    assert "Mock reply" in data["answer"]
    assert "POL-001" in data["sources"]

    app.dependency_overrides.clear()


def test_chat_unsupported_abstains():
    fake_assistant = BankAssistant(retriever=FakeRetriever(), generator=FakeGenerator())
    app.dependency_overrides[get_assistant] = lambda: fake_assistant

    response = client.post("/chat", json={"message": "Can I buy crypto?"})
    assert response.status_code == 200
    data = response.json()
    assert "cannot answer" in data["answer"].lower()
    assert data["sources"] == []

    app.dependency_overrides.clear()


def test_chat_invalid_empty_query():
    response = client.post("/chat", json={"message": ""})
    # Pydantic validation error
    assert response.status_code == 422