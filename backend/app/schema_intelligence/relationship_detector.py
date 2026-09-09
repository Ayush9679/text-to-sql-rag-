"""Multi-table schema relationship and foreign key inference engine."""

from typing import Any
from pydantic import BaseModel, Field
from app.dataset.profiler import TableProfile


class InferredRelationship(BaseModel):
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    relationship_type: str = "MANY_TO_ONE"  # MANY_TO_ONE, ONE_TO_ONE, ONE_TO_MANY
    confidence: float = 1.0
    description: str = ""


class RelationshipDetector:
    """Discovers relationships across tables using naming patterns, keys, and value domains."""

    def detect_relationships(
        self,
        table_profiles: list[TableProfile],
        table_samples: dict[str, dict[str, list[Any]]] | None = None,
    ) -> list[InferredRelationship]:
        relationships: list[InferredRelationship] = []
        table_map = {tp.table_name: tp for tp in table_profiles}

        for source_table, source_prof in table_map.items():
            for source_col in source_prof.columns:
                src_name = source_col.normalized_name

                # Look for target tables
                for target_table, target_prof in table_map.items():
                    if source_table == target_table:
                        continue

                    # Direct naming match: e.g. sales.customer_id -> customers.id or customers.customer_id
                    target_pk_candidates = target_prof.primary_key_candidates or ["id", f"{target_table}_id"]
                    
                    matched_target_col = None
                    confidence = 0.0

                    # 1. Exact column name match (e.g. customer_id == customer_id)
                    target_col_names = [c.normalized_name for c in target_prof.columns]
                    if src_name in target_col_names and (src_name in target_pk_candidates or src_name.endswith("_id") or src_name == "id"):
                        matched_target_col = src_name
                        confidence = 0.95
                    
                    # 2. Table prefix match (e.g. sales.customer_id -> customers.id or customer.id)
                    stem = target_table.rstrip("s")
                    if not matched_target_col and (src_name == f"{stem}_id" or src_name == f"{target_table}_id"):
                        if "id" in target_col_names:
                            matched_target_col = "id"
                            confidence = 0.90
                        elif f"{target_table}_id" in target_col_names:
                            matched_target_col = f"{target_table}_id"
                            confidence = 0.90
                        elif f"{stem}_id" in target_col_names:
                            matched_target_col = f"{stem}_id"
                            confidence = 0.90

                    # 3. If sample values are provided, check value overlap
                    if matched_target_col and table_samples:
                        src_vals = set(table_samples.get(source_table, {}).get(src_name, []))
                        tgt_vals = set(table_samples.get(target_table, {}).get(matched_target_col, []))
                        if src_vals and tgt_vals:
                            overlap = len(src_vals & tgt_vals) / len(src_vals)
                            if overlap > 0.8:
                                confidence = min(1.0, confidence + 0.05)
                            elif overlap < 0.2:
                                confidence = max(0.4, confidence - 0.3)

                    if matched_target_col and confidence >= 0.70:
                        relationships.append(
                            InferredRelationship(
                                source_table=source_table,
                                source_column=src_name,
                                target_table=target_table,
                                target_column=matched_target_col,
                                relationship_type="MANY_TO_ONE",
                                confidence=round(confidence, 2),
                                description=f"Join path: {source_table}.{src_name} -> {target_table}.{matched_target_col}",
                            )
                        )

        return relationships
