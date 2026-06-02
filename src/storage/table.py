import threading
from collections.abc import Iterator
from typing import Literal, TypeAlias, TypedDict

DBValue: TypeAlias = str | int | float | bool | None
Row: TypeAlias = dict[str, DBValue]

Operator: TypeAlias = Literal["=", ">", "<", ">=", "<=", "!=", "<>"]


class Condition(TypedDict, total=False):
    operator: Operator
    value: DBValue


WhereValue: TypeAlias = DBValue | Condition
WhereClause: TypeAlias = dict[str, WhereValue]


class Table:
    def __init__(self, name: str, columns: list[str]) -> None:
        self.name = name
        self.columns = columns
        self.columns_set: set[str] = set(
            columns
        )  # I am tryin to use this for searching if the cols in select where condition actually exists in this table

        # In-memory storage. A list of dictionaries representing rows.
        # TODO upgrade this to a B-Tree for indexing

        self.rows: list[Row] = []

        # CONCURRENCY
        # won't `asyncio`, going to use threads, you MUST lock the table before writing to prevent memory corruption if two multiple requests try to insert at the exact same millisecond
        self.lock = threading.Lock()  # creates a Mutex

    def insert(self, columns: list[str], values: list[DBValue]) -> Row:
        if len(columns) != len(values):
            raise ValueError("Column count does not match value count")

        row = dict(zip(columns, values))

        # Acquire the lock. If another thread is currently writing to this
        # table, this thread will pause (context switch) and wait here.
        with self.lock:
            self.rows.append(row)
            return row

    def select(self, columns: list[str], where: WhereClause) -> Iterator[Row]:
        # Validate columns in WHERE clause

        for col in columns:
            if col not in self.columns_set:
                raise ValueError(f"Column '{col}' does not exist in this table")

        # Instead of throwing an error for no data, an empty table
        # should simply yield nothing (which results in an empty list later)

        # Validate columns in WHERE clause
        for col in where:
            if col not in self.columns_set:
                raise ValueError(f"Column '{col}' does not exist in this table")

        # O(N) Table Scan
        for row in self.rows:
            match = True  # Assume the row matches until proven otherwise

            # 1. Check ALL conditions in the WHERE clause (AND logic)
            for col, condition in where.items():
                row_value = row.get(col)

                # Extract operator and value safely
                if isinstance(condition, dict):
                    operator = condition.get("operator", "=")
                    target_value = condition.get("value")
                else:
                    # Fallback just in case 'where' is formatted like {"department": "Sales"}
                    operator = "="
                    target_value = condition

                # 2. FIXED OPERATOR LOGIC: Compare row value (v) against target (value)
                if not self._compare(row_value, operator, target_value):
                    match = False
                    break

            # 3. If all conditions matched, yield the selected columns
            if match:
                # Dictionary comprehension to quickly grab only requested columns
                required_data: Row = {col: row.get(col) for col in columns}

                # 4. YIELD instead of return. This makes it a generator!
                yield required_data

    def _compare(
        self, row_value: DBValue, operator: Operator, target_value: DBValue
    ) -> bool:
        if operator == "=":
            return row_value == target_value

        if operator in ("!=", "<>"):
            return row_value != target_value

        if row_value is None or target_value is None:
            return False

        if not isinstance(row_value, int | float | str):
            return False

        if not isinstance(target_value, int | float | str):
            return False

        if type(row_value) is not type(target_value):
            return False

        try:
            row_value = float(row_value)  # noqa: F841
            target_value = float(target_value)

        except ValueError:
            return False

        if operator == ">":
            return row_value > target_value

        if operator == "<":
            return row_value < target_value

        if operator == ">=":
            return row_value >= target_value

        if operator == "<=":
            return row_value <= target_value

        return False
