"""Orchestration for the completed Business Text-to-SQL Analytics Pipeline."""

from collections.abc import Callable, Sequence
from typing import Any

from app.application.models import QueryRequest, QueryResponse, QueryStatus
from app.clarification.analyzer import QueryAnalyzer
from app.clarification.engine import ClarificationEngine
from app.clarification.models import ClarificationState, QueryAnalysis
from app.confidence.engine import ConfidenceEngine
from app.conversation.manager import ConversationManager, ConversationTurn
from app.response.answer_generator import AnswerGenerator
from app.schema_intelligence.models import DatabaseSchema
from app.schema_retrieval.documents import KnowledgeDocument, SchemaDocument
from app.schema_retrieval.service import SchemaRetrievalService
from app.sql_execution.models import ExecutionRequest
from app.sql_execution.service import SQLExecutionService
from app.sql_generation.models import SQLGenerationRequest
from app.sql_generation.service import SQLGenerationService


Document = SchemaDocument | KnowledgeDocument


class ApplicationQueryService:
    """Coordinates Clarification, Semantic Retrieval, Text-to-SQL, Execution, Confidence Scoring, and Answer Generation."""

    def __init__(
        self,
        *,
        schema: DatabaseSchema,
        documents: Sequence[Document],
        analyzer: QueryAnalyzer | None = None,
        clarification_engine: ClarificationEngine | None = None,
        retrieval_service: SchemaRetrievalService | None = None,
        sql_generation_service: SQLGenerationService | None = None,
        execution_service: SQLExecutionService | None = None,
        document_provider: Callable[[DatabaseSchema], Sequence[Document]] | None = None,
        confidence_engine: ConfidenceEngine | None = None,
        answer_generator: AnswerGenerator | None = None,
        conversation_manager: ConversationManager | None = None,
    ):
        self.schema = schema
        self.documents = list(documents)
        self.document_provider = document_provider
        self.clarification_engine = clarification_engine or ClarificationEngine()
        if analyzer is not None:
            self.clarification_engine.analyzer = analyzer
        engine_analyzer = getattr(self.clarification_engine, "analyzer", None)
        if engine_analyzer is not None and hasattr(engine_analyzer, "configure_schema"):
            engine_analyzer.configure_schema(schema.tables)
        self.retrieval_service = retrieval_service or SchemaRetrievalService()
        self.sql_generation_service = sql_generation_service or SQLGenerationService()
        if execution_service is None:
            raise ValueError("execution_service is required")
        self.execution_service = execution_service
        self.confidence_engine = confidence_engine or ConfidenceEngine()
        self.answer_generator = answer_generator or AnswerGenerator()
        self.conversation_manager = conversation_manager or ConversationManager()

    def handle(self, request: QueryRequest) -> QueryResponse:
        """Process a request or one existing clarification turn."""

        # 1. Conversational Query Refinement
        refined_query = self.conversation_manager.refine_query(
            request.query,
            conversation_id=request.conversation_id,
        )

        # 2. Clarification Engine
        state, decision, question = self._clarify(request, refined_query)
        if state is None:
            return self._failure("Query analysis failed.")
        if decision.action == "unsupported":
            return self._failure("This query is outside the supported analytical domain.", state=state)
        if decision.action == "clarify":
            return QueryResponse(
                status=QueryStatus.CLARIFICATION_REQUIRED,
                clarification=question,
                clarification_state=state,
                explanation=decision.reason,
            )
        if decision.action != "proceed" or state.analysis is None:
            return self._failure("Query analysis could not be completed.", state=state)

        analysis = state.analysis

        # 3. Semantic RAG Retrieval
        try:
            documents = (
                list(self.document_provider(self.schema))
                if self.document_provider is not None
                else self.documents
            )
            context = self.retrieval_service.retrieve_context(
                query=analysis.query,
                documents=documents,
            )
        except Exception:
            return self._failure("Schema retrieval failed.", state=state)

        # 4. Text-to-SQL Generation
        generation_request = self._generation_request(analysis, request, context.text)
        try:
            generation = self.sql_generation_service.generate(generation_request, self.schema)
        except Exception:
            return self._failure("SQL generation failed.", state=state)
        if generation.confidence <= 0.0 or not generation.sql.strip():
            return self._failure(generation.explanation or "SQL generation failed.", state=state)

        # 5. Safe SQL Execution
        try:
            execution = self.execution_service.execute(
                ExecutionRequest(
                    sql=generation.sql,
                    max_rows=request.max_rows,
                    dialect=request.dialect,
                )
            )
        except Exception:
            return self._failure("SQL execution failed.", sql=generation.sql, state=state)
        if not execution.success:
            return self._failure(
                execution.error or "SQL execution failed.",
                sql=generation.sql,
                state=state,
            )

        # 6. Multi-Signal Confidence Scoring
        raw_rows = [[r.get(c) for c in execution.columns] for r in execution.rows]
        conf_eval = self.confidence_engine.evaluate(
            retrieval_score=context.coverage if hasattr(context, "coverage") else 1.0,
            schema_match_ratio=1.0,
            sql_valid=True,
            execution_success=execution.success,
            row_count=execution.row_count,
            ambiguity_detected=False,
            llm_confidence=generation.confidence,
        )

        # 7. Natural-Language Answer Generation & Chart Selection
        answer_payload = self.answer_generator.generate_answer(
            query=request.query,
            sql=generation.sql,
            columns=execution.columns,
            rows=raw_rows,
            intent=analysis.intent,
        )

        # 8. Record in Conversation Memory
        if request.conversation_id:
            self.conversation_manager.record_turn(
                conversation_id=request.conversation_id,
                business_id="default",
                turn=ConversationTurn(
                    user_query=request.query,
                    standalone_query=analysis.query,
                    generated_sql=generation.sql,
                    intent=analysis.intent,
                    tables_used=generation.tables_used,
                    columns_used=generation.columns_used,
                    answer_summary=answer_payload.summary,
                ),
            )

        return QueryResponse(
            status=QueryStatus.SUCCESS,
            sql=generation.sql,
            columns=execution.columns,
            rows=execution.rows,
            row_count=execution.row_count,
            clarification_state=state,
            explanation=answer_payload.summary or generation.explanation,
            metadata={
                "tables_used": generation.tables_used,
                "columns_used": generation.columns_used,
                "retrieved_document_ids": [item.document_id for item in context.documents],
                "confidence": conf_eval.composite_score if conf_eval.composite_score > 0 else generation.confidence,
                "confidence_breakdown": conf_eval.model_dump(),
                "execution_time_ms": execution.execution_time_ms,
                "truncated": execution.truncated,
                "recommended_chart": answer_payload.recommended_chart,
                "key_highlights": answer_payload.key_highlights,
            },
        )

    def _clarify(self, request: QueryRequest, effective_query: str):
        try:
            if request.clarification_state is not None:
                if not request.clarification_answer or not request.clarification_answer.strip():
                    return None, None, None
                return self.clarification_engine.resolve_clarification(
                    state=request.clarification_state,
                    user_answer=request.clarification_answer,
                )
            return self.clarification_engine.process_query(
                effective_query,
                conversation_id=request.conversation_id,
            )
        except Exception:
            return None, None, None

    @staticmethod
    def _generation_request(
        analysis: QueryAnalysis,
        request: QueryRequest,
        schema_context: str,
    ) -> SQLGenerationRequest:
        return SQLGenerationRequest(
            query=analysis.query,
            intent=analysis.intent,
            entities=analysis.entities,
            metrics=analysis.metrics,
            filters=analysis.filters,
            aggregation=analysis.aggregation,
            sort_direction=analysis.sort_direction,
            limit=analysis.limit,
            schema_context=schema_context,
            dialect=request.dialect,
        )

    @staticmethod
    def _failure(
        explanation: str,
        *,
        sql: str | None = None,
        state: ClarificationState | None = None,
    ) -> QueryResponse:
        return QueryResponse(
            status=QueryStatus.FAILED,
            sql=sql,
            clarification_state=state,
            explanation=explanation,
        )
