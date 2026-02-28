import logging

from fastapi import APIRouter, HTTPException

from app.agents.orchestrator import OrchestratorError, process
from app.channels.adapter import from_web
from app.models.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a natural-language question about the family tree.

    The userId must correspond to an existing Person.id in Neo4j.
    """
    msg = from_web(request.message, request.user_id)
    try:
        reply = await process(msg.text, msg.sender_id)
    except OrchestratorError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in /chat")
        raise HTTPException(status_code=500, detail="Internal server error")
    return ChatResponse(reply=reply)
