import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from app.clarification.models import (
    ClarificationQuestion,
    ClarificationState,
    ClarificationTurn,
    QueryAnalysis,
)


class ClarificationStateManager:
    def create_state(
        self,
        original_query: str,
        analysis: Optional[QueryAnalysis] = None,
        conversation_id: Optional[str] = None,
    ) -> ClarificationState:
        return ClarificationState(
            conversation_id=conversation_id or str(uuid.uuid4()),
            original_query=original_query,
            current_query=original_query,
            analysis=analysis,
            pending_clarifications=[],
            resolved_fields={},
            clarification_history=[],
            status="awaiting_clarification",
        )

    def add_question(
        self,
        state: ClarificationState,
        question: ClarificationQuestion,
    ) -> ClarificationState:
        state.pending_clarifications.append(question)
        state.status = "awaiting_clarification"
        return state

    def resolve_question(
        self,
        state: ClarificationState,
        question: ClarificationQuestion,
        user_answer: str,
        resolved_field: str,
        resolved_value: Any,
    ) -> ClarificationState:
        # Record turn in history
        turn = ClarificationTurn(
            question=question,
            user_answer=user_answer,
            resolved_field=resolved_field,
            resolved_value=resolved_value,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        state.clarification_history.append(turn)
        state.resolved_fields[resolved_field] = resolved_value

        # Remove from pending clarifications
        state.pending_clarifications = [
            q for q in state.pending_clarifications if q.target_field != resolved_field
        ]

        if not state.pending_clarifications:
            state.status = "resolved"

        return state

    def cancel_state(self, state: ClarificationState) -> ClarificationState:
        state.status = "cancelled"
        state.pending_clarifications.clear()
        return state
