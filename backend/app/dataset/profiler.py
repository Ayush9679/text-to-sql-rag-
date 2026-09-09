"""Deep CSV and tabular data profiler for semantic inference and statistical analysis."""

import math
import re
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from pydantic import BaseModel, Field


class ColumnProfile(BaseModel):
    name: str
    normalized_name: str
    inferred_type: str  # INTEGER, BIGINT, NUMERIC, BOOLEAN, DATE, TIMESTAMP, TEXT
    semantic_type: str  # identifier, monetary, quantity, status, category, date, email, name, description, percentage, unknown
    null_count: int
    null_percentage: float
    unique_count: int
    cardinality_ratio: float
    is_primary_key_candidate: bool
    is_foreign_key_candidate: bool
    sample_values: list[Any] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)
    anomalies: list[str] = Field(default_factory=list)
    description: str = ""


class TableProfile(BaseModel):
    table_name: str
    row_count: int
    column_count: int
    columns: list[ColumnProfile] = Field(default_factory=list)
    primary_key_candidates: list[str] = Field(default_factory=list)
    foreign_key_candidates: list[str] = Field(default_factory=list)
    data_quality_issues: list[str] = Field(default_factory=list)


class DataProfiler:
    """Performs deep profiling on rows and columns of CSV datasets."""

    SEMANTIC_KEYWORDS = {
        "monetary": ["price", "amount", "amt", "cost", "revenue", "sales", "fee", "salary", "spend", "total", "subtotal", "tax", "discount"],
        "quantity": ["quantity", "qty", "count", "units", "volume", "num_", "number_of", "items"],
        "identifier": ["id", "_id", "code", "sku", "uuid", "guid", "key", "number", "no"],
        "status": ["status", "state", "flag", "stage", "is_", "active", "enabled", "cancelled", "completed"],
        "category": ["category", "type", "kind", "genre", "department", "tier", "segment", "group"],
        "date": ["date", "time", "created_at", "updated_at", "timestamp", "dob", "year", "month", "day", "period"],
        "percentage": ["rate", "percentage", "ratio", "pct", "discount_pct", "margin", "tax_rate"],
        "email": ["email", "e_mail", "mail"],
        "location": ["city", "state", "country", "region", "zip", "postal", "address", "zone", "territory"],
        "name": ["name", "title", "first_name", "last_name", "full_name", "customer_name", "product_name"],
    }

    def profile_column(
        self,
        name: str,
        normalized_name: str,
        values: list[str],
        total_rows: int,
    ) -> ColumnProfile:
        non_empty = [v.strip() for v in values if v is not None and v.strip() != ""]
        null_count = total_rows - len(non_empty)
        null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0

        unique_vals = set(non_empty)
        unique_count = len(unique_vals)
        cardinality_ratio = round(unique_count / total_rows, 4) if total_rows > 0 else 0.0

        inferred_type = self._infer_data_type(non_empty)
        stats, anomalies = self._compute_stats(inferred_type, non_empty)
        
        # Primary key candidate heuristic: 100% unique, 0% null, identifier-like name or high cardinality
        is_pk = (null_count == 0) and (unique_count == total_rows) and total_rows > 0
        if is_pk and inferred_type not in {"INTEGER", "BIGINT", "TEXT"}:
            is_pk = False

        semantic_type = self._infer_semantic_type(normalized_name, inferred_type, non_empty, stats, is_pk)
        is_fk = (not is_pk) and ("_id" in normalized_name or normalized_name.endswith("id")) and inferred_type in {"INTEGER", "BIGINT", "TEXT"}

        # Generate human-readable semantic description
        description = self._generate_description(normalized_name, semantic_type, inferred_type, null_pct, stats)

        # Representative sample (up to 5 distinct values)
        sample_values = list(unique_vals)[:5]

        return ColumnProfile(
            name=name,
            normalized_name=normalized_name,
            inferred_type=inferred_type,
            semantic_type=semantic_type,
            null_count=null_count,
            null_percentage=null_pct,
            unique_count=unique_count,
            cardinality_ratio=cardinality_ratio,
            is_primary_key_candidate=is_pk,
            is_foreign_key_candidate=is_fk,
            sample_values=sample_values,
            stats=stats,
            anomalies=anomalies,
            description=description,
        )

    def profile_table(
        self,
        table_name: str,
        headers: list[str],
        normalized_headers: list[str],
        rows: list[list[str]],
    ) -> TableProfile:
        total_rows = len(rows)
        columns: list[ColumnProfile] = []
        pk_candidates: list[str] = []
        fk_candidates: list[str] = []
        data_quality_issues: list[str] = []

        for col_idx, (orig_name, norm_name) in enumerate(zip(headers, normalized_headers)):
            col_values = [rows[r_idx][col_idx] for r_idx in range(total_rows)]
            col_prof = self.profile_column(orig_name, norm_name, col_values, total_rows)
            columns.append(col_prof)

            if col_prof.is_primary_key_candidate:
                pk_candidates.append(norm_name)
            if col_prof.is_foreign_key_candidate:
                fk_candidates.append(norm_name)
            if col_prof.null_percentage > 20.0:
                data_quality_issues.append(f"Column '{norm_name}' has high null rate ({col_prof.null_percentage}%).")
            if col_prof.anomalies:
                data_quality_issues.extend([f"Column '{norm_name}': {a}" for a in col_prof.anomalies])

        return TableProfile(
            table_name=table_name,
            row_count=total_rows,
            column_count=len(headers),
            columns=columns,
            primary_key_candidates=pk_candidates,
            foreign_key_candidates=fk_candidates,
            data_quality_issues=data_quality_issues,
        )

    def _infer_data_type(self, values: list[str]) -> str:
        if not values:
            return "TEXT"

        lowered = {v.lower() for v in values}
        if lowered <= {"true", "false", "yes", "no", "1", "0", "t", "f"}:
            return "BOOLEAN"

        # Check integers
        if all(re.fullmatch(r"[+-]?\d+", v) for v in values):
            try:
                int_vals = [int(v) for v in values]
                if all(-(2**31) <= v <= 2**31 - 1 for v in int_vals):
                    return "INTEGER"
                return "BIGINT"
            except ValueError:
                pass

        # Check numeric / float / currency strings (e.g. "$1,234.50" or "1234.56")
        cleaned_numeric = [v.replace("$", "").replace("₹", "").replace("€", "").replace("£", "").replace(",", "") for v in values]
        is_numeric = True
        for v in cleaned_numeric:
            try:
                Decimal(v)
            except (InvalidOperation, ValueError):
                is_numeric = False
                break
        if is_numeric:
            return "NUMERIC"

        # Check date
        if all(self._parse_date(v) is not None for v in values):
            return "DATE"

        # Check timestamp
        if all(self._parse_datetime(v) is not None for v in values):
            return "TIMESTAMP"

        return "TEXT"

    def _compute_stats(self, inferred_type: str, values: list[str]) -> tuple[dict[str, Any], list[str]]:
        stats: dict[str, Any] = {}
        anomalies: list[str] = []
        if not values:
            return stats, anomalies

        if inferred_type in {"INTEGER", "BIGINT", "NUMERIC"}:
            try:
                nums = [float(v.replace("$", "").replace("₹", "").replace("€", "").replace("£", "").replace(",", "")) for v in values]
                nums.sort()
                n = len(nums)
                total = sum(nums)
                mean_val = total / n
                median_val = nums[n // 2] if n % 2 != 0 else (nums[n // 2 - 1] + nums[n // 2]) / 2.0
                min_val = nums[0]
                max_val = nums[-1]

                # Standard deviation
                variance = sum((x - mean_val) ** 2 for x in nums) / n if n > 1 else 0.0
                std_dev = math.sqrt(variance)

                stats = {
                    "min": min_val,
                    "max": max_val,
                    "mean": round(mean_val, 2),
                    "median": round(median_val, 2),
                    "std_dev": round(std_dev, 2),
                }

                # Outlier detection (IQR rule)
                if n >= 10:
                    q1 = nums[n // 4]
                    q3 = nums[(3 * n) // 4]
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    outliers = [x for x in nums if x < lower_bound or x > upper_bound]
                    if len(outliers) > 0 and len(outliers) <= (0.05 * n):
                        anomalies.append(f"{len(outliers)} statistical outlier(s) detected outside range [{lower_bound:.2f}, {upper_bound:.2f}].")
            except Exception:
                pass

        elif inferred_type == "TEXT":
            counts = Counter(values).most_common(5)
            stats = {
                "top_categories": [{"value": val, "frequency": count} for val, count in counts],
                "avg_string_length": round(sum(len(v) for v in values) / len(values), 1),
            }

        return stats, anomalies

    def _infer_semantic_type(
        self,
        name: str,
        inferred_type: str,
        values: list[str],
        stats: dict[str, Any],
        is_pk: bool,
    ) -> str:
        name_lower = name.lower()

        if is_pk or name_lower.endswith("_id") or name_lower == "id" or "code" in name_lower or "sku" in name_lower:
            return "identifier"

        for sem_type, keywords in self.SEMANTIC_KEYWORDS.items():
            if any(k in name_lower for k in keywords):
                return sem_type

        if inferred_type in {"DATE", "TIMESTAMP"}:
            return "date"

        if inferred_type in {"INTEGER", "BIGINT", "NUMERIC"}:
            if "min" in stats and stats["min"] >= 0 and "max" in stats and stats["max"] <= 100 and ("rate" in name_lower or "pct" in name_lower):
                return "percentage"
            return "quantity" if inferred_type in {"INTEGER", "BIGINT"} else "monetary"

        if inferred_type == "TEXT":
            unique_count = len(set(values))
            if unique_count <= 20 and len(values) > 50:
                return "category"
            return "description"

        return "unknown"

    def _generate_description(
        self,
        name: str,
        semantic_type: str,
        inferred_type: str,
        null_pct: float,
        stats: dict[str, Any],
    ) -> str:
        readable_name = name.replace("_", " ").title()
        desc = f"{readable_name} ({inferred_type})"
        if semantic_type != "unknown":
            desc += f" representing {semantic_type.replace('_', ' ')}"
        if stats and "min" in stats and "max" in stats:
            desc += f" ranging from {stats['min']} to {stats['max']}"
        if null_pct > 0:
            desc += f" [{null_pct}% nulls]"
        return desc

    @staticmethod
    def _parse_date(value: str) -> date | None:
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
        for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%b %d, %Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None
