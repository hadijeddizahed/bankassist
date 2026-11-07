import json
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status
from bankassist.core import BankAssistant, KeywordRetriever, ExtractiveGenerator, Document
from bankassist.schemas import ChatRequest, ChatResponse


app = FastAPI(title="BankAssistant API", version="0.1.0")



def load_default_documents() -> list[Document]:
    policy_path = Path(__file__).resolve().parent.parent / "data" / "policies.json"
    if not policy_path.exists():
        return []
    with open(policy_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    return [Document(id=item["id"], text=item["text"]) for item in raw_data]

def get_assistant()->BankAssistant:
    """Dependency provider. Swappable in tests with app.dependency_overrides."""
    documents = load_default_documents()
    retriever = KeywordRetriever(documents)
    generator = ExtractiveGenerator()
    return BankAssistant(retriever, generator)


@app.post("/chat")
async def chat_endpoint(
        request: ChatRequest,
        assistant: BankAssistant = Depends(get_assistant),
)->ChatResponse:
    try:
        result = assistant.answer(request.message)
        return ChatResponse(
            answer = result.text,
            sources= list(result.sources),
            session_id= request.session_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing the chat request."
        )

