"""Conversational threads and multi-turn state routes."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import require_authenticated, require_csrf
from app.auth import AuthenticatedContext
from app.conversation.manager import ConversationManager

router = APIRouter(prefix="/conversations", tags=["Conversations"])
conversation_manager = ConversationManager()


class CreateConversationPayload(BaseModel):
    title: str = "New Analysis"


@router.post("", status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: CreateConversationPayload,
    context: AuthenticatedContext = Depends(require_authenticated),
    _csrf: None = Depends(require_csrf),
) -> dict:
    conversation_id = str(uuid.uuid4())
    ctx = conversation_manager.get_or_create(conversation_id, context.business_id)
    return {
        "id": conversation_id,
        "title": payload.title,
        "business_id": context.business_id,
        "turns_count": len(ctx.turns),
    }


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str,
    context: AuthenticatedContext = Depends(require_authenticated),
) -> dict:
    ctx = conversation_manager.get_or_create(conversation_id, context.business_id)
    return {
        "id": ctx.conversation_id,
        "business_id": ctx.business_id,
        "turns": [t.model_dump(mode="json") for t in ctx.turns],
        "active_tables": ctx.active_tables,
        "active_metrics": ctx.active_metrics,
        "active_filters": ctx.active_filters,
    }
