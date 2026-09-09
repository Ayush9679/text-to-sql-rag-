import pytest

from app.sql_generation.recovery import (
    RecoveryAttempt,
    RecoveryDecision,
    SQLRecoveryManager,
)


def test_default_retry_limit():

    manager = SQLRecoveryManager()

    assert (
        manager.max_retries == 2
    )

    assert (
        manager.attempt_count == 0
    )

    assert manager.attempts == ()


def test_negative_retry_limit_rejected():

    with pytest.raises(
        ValueError,
        match="max_retries cannot be negative",
    ):

        SQLRecoveryManager(
            max_retries=-1
        )


def test_record_failure():

    manager = SQLRecoveryManager()

    attempt = manager.record_failure(
        sql=(
            "SELECT customer_name "
            "FROM analytics.customers;"
        ),
        errors=[
            "Unknown column: customer_name",
        ],
    )

    assert isinstance(
        attempt,
        RecoveryAttempt,
    )

    assert attempt.attempt == 1

    assert (
        attempt.sql
        == (
            "SELECT customer_name "
            "FROM analytics.customers;"
        )
    )

    assert attempt.errors == (
        "Unknown column: customer_name",
    )

    assert (
        manager.attempt_count == 1
    )

    assert len(
        manager.attempts
    ) == 1


def test_multiple_failures_are_tracked():

    manager = SQLRecoveryManager()

    manager.record_failure(
        sql="SELECT bad_column FROM customers;",
        errors=[
            "Unknown column: bad_column",
        ],
    )

    manager.record_failure(
        sql="SELECT customer_id FROM bad_table;",
        errors=[
            "Unknown table: bad_table",
        ],
    )

    assert (
        manager.attempt_count == 2
    )

    assert (
        manager.attempts[0].attempt
        == 1
    )

    assert (
        manager.attempts[1].attempt
        == 2
    )


def test_retry_allowed_after_first_failure():

    manager = SQLRecoveryManager(
        max_retries=2
    )

    manager.record_failure(
        sql="SELECT bad_column FROM customers;",
        errors=[
            "Unknown column: bad_column",
        ],
    )

    decision = manager.decide()

    assert isinstance(
        decision,
        RecoveryDecision,
    )

    assert (
        decision.should_retry is True
    )

    assert (
        decision.next_attempt == 2
    )


def test_retry_allowed_after_second_failure():

    manager = SQLRecoveryManager(
        max_retries=2
    )

    manager.record_failure(
        sql="SELECT bad_column FROM customers;",
        errors=[
            "Unknown column: bad_column",
        ],
    )

    manager.record_failure(
        sql="SELECT another_bad_column FROM customers;",
        errors=[
            "Unknown column: another_bad_column",
        ],
    )

    decision = manager.decide()

    assert (
        decision.should_retry is True
    )

    assert (
        decision.next_attempt == 3
    )


def test_retry_stops_after_maximum_retries():

    manager = SQLRecoveryManager(
        max_retries=2
    )

    manager.record_failure(
        sql="SELECT bad_column FROM customers;",
        errors=[
            "Unknown column: bad_column",
        ],
    )

    manager.record_failure(
        sql="SELECT another_bad_column FROM customers;",
        errors=[
            "Unknown column: another_bad_column",
        ],
    )

    manager.record_failure(
        sql="SELECT third_bad_column FROM customers;",
        errors=[
            "Unknown column: third_bad_column",
        ],
    )

    decision = manager.decide()

    assert (
        decision.should_retry is False
    )

    assert (
        decision.next_attempt == 3
    )

    assert (
        "Maximum SQL generation retries"
        in decision.reason
    )


def test_zero_retries_disables_recovery():

    manager = SQLRecoveryManager(
        max_retries=0
    )

    manager.record_failure(
        sql="SELECT bad_column FROM customers;",
        errors=[
            "Unknown column: bad_column",
        ],
    )

    decision = manager.decide()

    assert (
        decision.should_retry is False
    )


def test_retry_prompt_contains_original_query():

    manager = SQLRecoveryManager()

    prompt = manager.build_retry_prompt(
        original_query=(
            "Return 10 customers"
        ),
        sql=(
            "SELECT customer_name "
            "FROM analytics.customers;"
        ),
        errors=[
            "Unknown column: customer_name",
        ],
    )

    assert (
        "Return 10 customers"
        in prompt
    )


def test_retry_prompt_contains_previous_sql():

    manager = SQLRecoveryManager()

    prompt = manager.build_retry_prompt(
        original_query=(
            "Return 10 customers"
        ),
        sql=(
            "SELECT customer_name "
            "FROM analytics.customers;"
        ),
        errors=[
            "Unknown column: customer_name",
        ],
    )

    assert (
        "SELECT customer_name"
        in prompt
    )

    assert (
        "analytics.customers"
        in prompt
    )


def test_retry_prompt_contains_validation_errors():

    manager = SQLRecoveryManager()

    prompt = manager.build_retry_prompt(
        original_query=(
            "Return 10 customers"
        ),
        sql=(
            "SELECT customer_name "
            "FROM analytics.customers;"
        ),
        errors=[
            "Unknown column: customer_name",
        ],
    )

    assert (
        "Unknown column: customer_name"
        in prompt
    )


def test_retry_prompt_contains_schema_context():

    manager = SQLRecoveryManager()

    prompt = manager.build_retry_prompt(
        original_query=(
            "Return 10 customers"
        ),
        sql=(
            "SELECT customer_name "
            "FROM analytics.customers;"
        ),
        errors=[
            "Unknown column: customer_name",
        ],
        schema_context=(
            "TABLE analytics.customers\n"
            "COLUMNS customer_id, first_name"
        ),
    )

    assert (
        "analytics.customers"
        in prompt
    )

    assert (
        "customer_id"
        in prompt
    )


def test_retry_prompt_contains_business_context():

    manager = SQLRecoveryManager()

    prompt = manager.build_retry_prompt(
        original_query=(
            "Return 10 customers"
        ),
        sql=(
            "SELECT customer_name "
            "FROM analytics.customers;"
        ),
        errors=[
            "Unknown column: customer_name",
        ],
        business_context=(
            "A customer is a registered user."
        ),
    )

    assert (
        "A customer is a registered user."
        in prompt
    )


def test_retry_prompt_forbids_destructive_sql():

    manager = SQLRecoveryManager()

    prompt = manager.build_retry_prompt(
        original_query=(
            "Return 10 customers"
        ),
        sql=(
            "DELETE FROM analytics.customers;"
        ),
        errors=[
            "Destructive SQL is not allowed."
        ],
    )

    prompt_lower = prompt.lower()

    assert (
        "do not use insert"
        in prompt_lower
    )

    assert (
        "update"
        in prompt_lower
    )

    assert (
        "delete"
        in prompt_lower
    )

    assert (
        "drop"
        in prompt_lower
    )


def test_retry_prompt_requires_sql_only():

    manager = SQLRecoveryManager()

    prompt = manager.build_retry_prompt(
        original_query=(
            "Return 10 customers"
        ),
        sql="",
        errors=[
            "No SQL statement found."
        ],
    )

    assert (
        "Return only the SQL statement."
        in prompt
    )

    assert (
        "Do not use Markdown code fences."
        in prompt
    )


def test_reset_clears_attempts():

    manager = SQLRecoveryManager()

    manager.record_failure(
        sql="SELECT bad_column FROM customers;",
        errors=[
            "Unknown column: bad_column",
        ],
    )

    assert (
        manager.attempt_count == 1
    )

    manager.reset()

    assert (
        manager.attempt_count == 0
    )

    assert manager.attempts == ()


def test_recovery_summary_without_attempts():

    manager = SQLRecoveryManager()

    assert (
        manager.recovery_summary()
        == "No recovery attempts recorded."
    )


def test_recovery_summary_with_attempts():

    manager = SQLRecoveryManager()

    manager.record_failure(
        sql="SELECT bad_column FROM customers;",
        errors=[
            "Unknown column: bad_column",
        ],
    )

    manager.record_failure(
        sql="SELECT bad_table FROM orders;",
        errors=[
            "Unknown table: orders",
        ],
    )

    summary = (
        manager.recovery_summary()
    )

    assert (
        "Attempt 1:"
        in summary
    )

    assert (
        "Attempt 2:"
        in summary
    )

    assert (
        "Unknown column: bad_column"
        in summary
    )

    assert (
        "Unknown table: orders"
        in summary
    )