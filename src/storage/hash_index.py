import secrets
import threading
from typing import Any, Dict
from datetime import datetime, timezone


class HashIndexTable:
    def __init__(self, name: str, columns:list[str], primary_key: str=None)-> None:
        self.name = name
        self.columns = columns
        self.columns_set = set(columns) # I am tryin to use this for searching if the cols in select where condition actually exists in this table

        
        # In-memory storage. A list of dictionaries representing rows.
        # TODO upgrade this to a B-Tree for indexing

        self.rows:list[Dict[str, Any]] = []

        # CONCURRENCY
        # won't asyncio, going to use threads, MUST lock the table before writing to prevent memory corruption if two multiple requests try to insert at the exact same millisecond
        self.lock = threading.Lock() # creates a Mutex

        self.indexes = {}

        if primary_key:
            # auto create hash index for the primary key
            self.indexes[primary_key] = {} # { 5: reference to row dict }, {col_name: {"col_value": entire row}}

    def insert(self, columns: list[str], values: list[Any])-> Dict[str, Any]:
        if len(columns) != len(values):
            raise ValueError("Column count does not match value count")
        
        row = dict(zip(columns, values))

        # Acquire the lock. If another thread is currently writing to this 
        # table, this thread will pause (context switch) and wait here.
        with self.lock:
            self.rows.append(row)
            
            for col_name, index_dict in self.indexes.items():
                #  check if the col is indexed 
                if col_name in row:
                    col_value = row[col_name]
                    index_dict[col_value] = row


            return row
        
    def select(self, columns: list[str], where: Dict[str, Any]):
        # Validate columns in WHERE clause where = {col: {operator:"", value:any}}
        condition_cols = set(where.keys())
        for col in condition_cols:
            if col not in self.columns_set:
                raise ValueError(f"Column '{col}' does not exist in this table")

        # Instead of throwing an error for no data, an empty table 
        # should simply yield nothing (which results in an empty list later)

        index_row_id_sets = [] # [{}, {}]

        #  before sequential scan check if self.indexes contain the column specified in the WHERE clause
        for col, condition in where.items():
            if col not in self.indexes:
                continue
            

            if isinstance(condition, dict):
                operator = condition.get("operator", "=")
                target_value = condition.get("value")
            else:
                operator = "="
                target_value = condition

            # Hash indexes can ONLY be used for equality '='
            if operator == "=":

                index_dict = self.indexes[col] # {5:row dict}

                row = index_dict.get(target_value) # O(1)

                if row is not None:
                    index_row_id_sets.append(row)
                   
                   
        if index_row_id_sets:
            candidate_row_ids = set.intersection(*index_row_id_sets)
            candidate_rows = [self.rows_by_id[row_id] for row_id in candidate_row_ids]
        else:
            candidate_rows = self.rows

        for row in candidate_rows:
            if self.row_matches_where(row, where):
                yield {col: row.get(col) for col in columns}

    def row_matches_where(self, row: Dict[str, Any], where: Dict[str, Any]) -> bool:
        for col, condition in where.items():
            row_value = row.get(col)

            if isinstance(condition, dict):
                operator = condition.get("operator", "=")
                target_value = condition.get("value")
            else:
                operator = "="
                target_value = condition

            if operator == "=" and not (row_value == target_value):
                return False
            elif operator == ">=" and not (row_value >= target_value):
                return False
            elif operator == "<=" and not (row_value <= target_value):
                return False
            elif operator in ("!=", "<>") and not (row_value != target_value):
                return False
            elif operator == ">" and not (row_value > target_value):
                return False
            elif operator == "<" and not (row_value < target_value):
                return False

        return True

