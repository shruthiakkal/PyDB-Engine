import secrets
import threading
from typing import Any, Dict, List
from datetime import datetime, timezone


class Table:
    def __init__(self, name: str, columns:List[str])-> None:
        self.name = name
        self.columns = columns
        self.columns_set = set(columns) # I am tryin to use this for searching if the cols in select where condition actually exists in this table

        
        # In-memory storage. A list of dictionaries representing rows.
        # TODO upgrade this to a B-Tree for indexing

        self.rows:List[Dict[str, Any]] = []

        # CONCURRENCY
        # won't `asyncio`, going to use threads, you MUST lock the table before writing to prevent memory corruption if two multiple requests try to insert at the exact same millisecond
        self.lock = threading.Lock() # creates a Mutex

    def insert(self, columns: List[str], values: List[Any])-> Dict[str, Any]:
        if len(columns) != len(values):
            raise ValueError("Column count does not match value count")
        
        row = dict(zip(columns, values))

        # Acquire the lock. If another thread is currently writing to this 
        # table, this thread will pause (context switch) and wait here.
        with self.lock:
            self.rows.append(row)
            return row
        
    def select(self, columns: List[str], where: Dict[str, Any]):
        # Validate columns in WHERE clause
        condition_cols = set(where.keys())
        for col in condition_cols:
            if col not in self.columns_set:
                raise ValueError(f"Column '{col}' does not exist in this table")

        # Instead of throwing an error for no data, an empty table 
        # should simply yield nothing (which results in an empty list later)
        
        # O(N) Table Scan
        for row in self.rows:
            match = True # Assume the row matches until proven otherwise
            
            # 1. Check ALL conditions in the WHERE clause (AND logic)
            for k, condition in where.items():
                v = row.get(k)
                
                # Extract operator and value safely
                if isinstance(condition, dict):
                    operator = condition.get("operator", "=")
                    value = condition.get("value")
                else:
                    # Fallback just in case 'where' is formatted like {"department": "Sales"}
                    operator = "="
                    value = condition
                
                # 2. FIXED OPERATOR LOGIC: Compare row value (v) against target (value)
                if operator == "=" and not (v == value):
                    match = False; break # Fails a condition, skip this row
                elif operator == ">=" and not (v >= value):
                    match = False; break
                elif operator == "<=" and not (v <= value):
                    match = False; break
                elif (operator == "!=" or operator == "<>") and not (v != value):
                    match = False; break
                elif operator == ">" and not (v > value):
                    match = False; break
                elif operator == "<" and not (v < value):
                    match = False; break
            
            # 3. If all conditions matched, yield the selected columns
            if match:
                # Dictionary comprehension to quickly grab only requested columns
                required_data = {col: row.get(col) for col in columns}
                
                # 4. YIELD instead of return. This makes it a generator!
                yield required_data

