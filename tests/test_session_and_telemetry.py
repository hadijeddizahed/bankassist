from bankassist.core import BankAssistant, Document
from bankassist.generator import MockLLMGenerator
from bankassist.session import InMemorySessionStore


def test_session_history_bounded():
    store = InMemorySessionStore(max_turns=4)
    session_id = "test_sess_1"

    for i in range(6):
        store.add_message(session_id, "user", f"Turn {i}")

    history = store.get_history(session_id)
    assert len(history) == 4
    assert history[0].text == "Turn 2"
    assert history[-1].text == "Turn 5"


def test_multi_turn_assistant_telemetry():
    docs = [Document(id="POL-001", text="Report lost card in the app.")]
    from bankassist.core import KeywordRetriever

    retriever = KeywordRetriever(docs)
    generator = MockLLMGenerator(model_id="test-mock")
    store = InMemorySessionStore(max_turns=4)
    assistant = BankAssistant(retriever, generator, session_store=store)

    session_id = "chat_123"
    # Turn 1
    ans1 = assistant.answer("How to report lost card?", session_id=session_id)
    assert ans1.model_id == "test-mock"
    assert ans1.prompt_version == "v1.0.0"
    assert ans1.latency_ms > 0
    assert "POL-001" in ans1.sources

    # Check store has recorded Turn 1
    history = store.get_history(session_id)
    assert len(history) == 2  # user + assistant

    # Turn 2
    ans2 = assistant.answer("Can you tell me more about lost card?", session_id=session_id)
    assert len(store.get_history(session_id)) == 4