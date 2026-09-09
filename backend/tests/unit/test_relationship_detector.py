"""Unit tests for RelationshipDetector."""

from app.dataset.profiler import ColumnProfile, TableProfile
from app.schema_intelligence.relationship_detector import RelationshipDetector


def test_detect_relationships_by_name_and_prefix():
    detector = RelationshipDetector()

    customers_table = TableProfile(
        table_name="customers",
        row_count=50,
        column_count=3,
        columns=[
            ColumnProfile(
                name="id",
                normalized_name="id",
                inferred_type="INTEGER",
                semantic_type="identifier",
                null_count=0,
                null_percentage=0.0,
                unique_count=50,
                cardinality_ratio=1.0,
                is_primary_key_candidate=True,
                is_foreign_key_candidate=False,
            ),
            ColumnProfile(
                name="name",
                normalized_name="name",
                inferred_type="TEXT",
                semantic_type="name",
                null_count=0,
                null_percentage=0.0,
                unique_count=50,
                cardinality_ratio=1.0,
                is_primary_key_candidate=False,
                is_foreign_key_candidate=False,
            ),
        ],
        primary_key_candidates=["id"],
    )

    sales_table = TableProfile(
        table_name="sales",
        row_count=200,
        column_count=4,
        columns=[
            ColumnProfile(
                name="sale_id",
                normalized_name="sale_id",
                inferred_type="INTEGER",
                semantic_type="identifier",
                null_count=0,
                null_percentage=0.0,
                unique_count=200,
                cardinality_ratio=1.0,
                is_primary_key_candidate=True,
                is_foreign_key_candidate=False,
            ),
            ColumnProfile(
                name="customer_id",
                normalized_name="customer_id",
                inferred_type="INTEGER",
                semantic_type="identifier",
                null_count=0,
                null_percentage=0.0,
                unique_count=45,
                cardinality_ratio=0.225,
                is_primary_key_candidate=False,
                is_foreign_key_candidate=True,
            ),
        ],
        primary_key_candidates=["sale_id"],
        foreign_key_candidates=["customer_id"],
    )

    relationships = detector.detect_relationships([customers_table, sales_table])
    assert len(relationships) == 1
    rel = relationships[0]
    assert rel.source_table == "sales"
    assert rel.source_column == "customer_id"
    assert rel.target_table == "customers"
    assert rel.target_column == "id"
    assert rel.confidence >= 0.85
