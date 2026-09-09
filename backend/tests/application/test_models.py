import pytest
from pydantic import ValidationError

from app.application.models import QueryRequest, QueryResponse, QueryStatus
from app.clarification.models import ClarificationQuestion


def test_query_request_and_success_response_are_serializable():
    request = QueryRequest(query="  Return customers  ", max_rows=10)
    response = QueryResponse(
        status=QueryStatus.SUCCESS,
        sql="SELECT customer_id FROM analytics.customers",
        columns=["customer_id"],
        rows=[{"customer_id": 1}],
        row_count=1,
    )

    assert request.query == "Return customers"
    assert response.model_dump(mode="json")["status"] == "success"


@pytest.mark.parametrize("query", ["", "   "])
def test_empty_query_is_rejected(query):
    with pytest.raises(ValidationError):
        QueryRequest(query=query)


def test_clarification_and_failure_responses_are_valid():
    clarification = QueryResponse(
        status=QueryStatus.CLARIFICATION_REQUIRED,
        clarification=ClarificationQuestion(
            question="What should determine the best customers?",
            reason="A ranking metric is required.",
            target_field="ranking_metric",
        ),
    )
    failure = QueryResponse(status=QueryStatus.FAILED, explanation="Schema retrieval failed.")

    assert clarification.clarification is not None
    assert failure.explanation == "Schema retrieval failed."
