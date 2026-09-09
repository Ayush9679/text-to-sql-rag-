from typing import Optional
from app.clarification.ambiguity import AmbiguityDetector
from app.clarification.analyzer import QueryAnalyzer
from app.clarification.decision import ClarificationDecisionEngine
from app.clarification.intent_validator import IntentValidator
from app.clarification.missing_information import MissingInformationDetector
from app.clarification.models import (
    ClarificationDecision,
    ClarificationQuestion,
    ClarificationState,
    QueryAnalysis,
)
from app.clarification.question_generator import ClarificationQuestionGenerator
from app.clarification.resolver import ClarificationResolver
from app.clarification.state import ClarificationStateManager
from app.schema_retrieval.context import RAGContext


class ClarificationEngine:
    def __init__(self):
        self.analyzer = QueryAnalyzer()
        self.validator = IntentValidator()
        self.ambiguity_detector = AmbiguityDetector()
        self.missing_detector = MissingInformationDetector()
        self.decision_engine = ClarificationDecisionEngine()
        self.question_generator = ClarificationQuestionGenerator()
        self.state_manager = ClarificationStateManager()
        self.resolver = ClarificationResolver()

    def process_query(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        rag_context: Optional[RAGContext] = None,
    ) -> tuple[ClarificationState, ClarificationDecision, Optional[ClarificationQuestion]]:
        # 1. Analyze query
        analysis = self.analyzer.analyze(query)

        # 2. Validate intent
        intent_val = self.validator.validate(analysis)

        # 3. Detect ambiguities
        ambiguity = self.ambiguity_detector.detect(analysis)

        # 4. Detect missing information
        missing_info = self.missing_detector.detect(analysis)

        # 5. Make decision
        decision = self.decision_engine.decide(
            analysis=analysis,
            intent_validation=intent_val,
            ambiguity=ambiguity,
            missing_info=missing_info,
            rag_context=rag_context,
        )

        # 6. Initialize state
        state = self.state_manager.create_state(
            original_query=query,
            analysis=analysis,
            conversation_id=conversation_id,
        )

        question: Optional[ClarificationQuestion] = None

        if decision.action == "clarify":
            state.status = "awaiting_clarification"
            question = self.question_generator.generate(
                decision=decision,
                analysis=analysis,
                rag_context=rag_context,
            )
            state.pending_clarifications = [question]
        elif decision.action == "proceed":
            state.status = "resolved"
        elif decision.action == "unsupported":
            state.status = "unsupported"

        return state, decision, question

    def resolve_clarification(
        self,
        state: ClarificationState,
        user_answer: str,
        target_field: Optional[str] = None,
        rag_context: Optional[RAGContext] = None,
    ) -> tuple[ClarificationState, ClarificationDecision, Optional[ClarificationQuestion]]:
        updated_state, decision = self.resolver.resolve(
            state=state,
            user_answer=user_answer,
            target_field=target_field,
            rag_context=rag_context,
        )
        next_question: Optional[ClarificationQuestion] = None
        if updated_state.pending_clarifications:
            next_question = updated_state.pending_clarifications[0]
        return updated_state, decision, next_question
