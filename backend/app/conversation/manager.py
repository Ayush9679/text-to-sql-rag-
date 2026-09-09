"""Conversational Analytics & Multi-turn query state manager."""

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    user_query: str
    standalone_query: str
    generated_sql: str | None = None
    intent: str | None = None
    tables_used: list[str] = Field(default_factory=list)
    columns_used: list[str] = Field(default_factory=list)
    filters: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    answer_summary: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationContext(BaseModel):
    conversation_id: str
    business_id: str
    turns: list[ConversationTurn] = Field(default_factory=list)
    active_filters: list[str] = Field(default_factory=list)
    active_tables: list[str] = Field(default_factory=list)
    active_metrics: list[str] = Field(default_factory=list)


class ConversationManager:
    """Maintains multi-turn context and refines conversational follow-up questions."""

    def __init__(self):
        self._conversations: dict[str, ConversationContext] = {}

    def get_or_create(self, conversation_id: str, business_id: str) -> ConversationContext:
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = ConversationContext(
                conversation_id=conversation_id,
                business_id=business_id,
            )
        return self._conversations[conversation_id]

    def record_turn(
        self,
        conversation_id: str,
        business_id: str,
        turn: ConversationTurn,
    ) -> None:
        ctx = self.get_or_create(conversation_id, business_id)
        ctx.turns.append(turn)
        if turn.tables_used:
            ctx.active_tables = list(set(ctx.active_tables + turn.tables_used))
        if turn.metrics:
            ctx.active_metrics = list(set(ctx.active_metrics + turn.metrics))
        if turn.filters:
            ctx.active_filters = list(set(ctx.active_filters + turn.filters))

    def refine_query(
        self,
        user_query: str,
        conversation_id: str | None = None,
        business_id: str = "default",
    ) -> str:
        """Determines if the query is a follow-up refinement and rewrites it into a standalone question."""
        if not conversation_id or conversation_id not in self._conversations:
            return user_query

        ctx = self._conversations[conversation_id]
        if not ctx.turns:
            return user_query

        last_turn = ctx.turns[-1]
        last_query = last_turn.standalone_query or last_turn.user_query
        q_lower = user_query.lower().strip()

        # Check for conversational follow-up patterns
        if q_lower.startswith(("only show", "filter by", "where", "only the ones", "just the ones", "exclude", "make that", "compare with", "break down by", "by city", "by month", "by region", "for delhi", "for mumbai")):
            if q_lower.startswith(("only show the ones from", "only show ones from", "only the ones from", "just the ones from")):
                target = q_lower.split("from")[-1].strip()
                return f"{last_query} filtered to location {target}"
            if q_lower.startswith("only show customers with"):
                condition = q_lower.replace("only show customers with", "").strip()
                return f"{last_query} where {condition}"
            if "make that monthly" in q_lower:
                return f"{last_query} broken down monthly"
            if "exclude cancelled" in q_lower:
                return f"{last_query} excluding cancelled orders"
            
            return f"{last_query} ({user_query})"

        return user_query
