import secrets
import threading
from typing import Any, Dict
from datetime import datetime, timezone


class HashIndexTable:
    def __init__(self, name: str, columns:list[str], primary_key: str=None)-> None:
        self.name = name
        self.columns = columns
        self.columns_set = set(columns) # I am tryin to use this for searching if the cols in select where condition actually exists in this table

        self.primary_key = primary_key
        
        # In-memory storage. A list of dictionaries representing rows.
        # TODO upgrade this to a B-Tree for indexing

        self.rows:list[Dict[str, Any]] = []

        # CONCURRENCY
        # won't asyncio, going to use threads, MUST lock the table before writing to prevent memory corruption if two multiple requests try to insert at the exact same millisecond
        self.lock = threading.Lock() # creates a Mutex

        self.indexes = {}

        if primary_key:
            # auto create hash index for the primary key
            self.indexes[primary_key] = {} # {col_name: {"col_value": [entire row1, row2, row3]}}

    def insert(self, columns: list[str], values: list[Any])-> Dict[str, Any]:
        if len(columns) != len(values):
            raise ValueError("Column count does not match value count")
        
        row = dict(zip(columns, values)) # {col_name1:value1, col_name2:value2}

        # Acquire the lock. If another thread is currently writing to this 
        # table, this thread will pause (context switch) and wait here.
        with self.lock:

            # primary key validation
            if self.primary_key and self.primary_key in row:
                pk_value = row[self.primary_key]
                pk_index = self.indexes.get(self.primary_key)

                if pk_value in pk_index and len(pk_index[pk_value]) > 0:
                    raise ValueError(f"Unique constraint violation: {self.primary_key} '{pk_value}' already exists.")



            self.rows.append(row)
            
            for col_name, index_dict in self.indexes.items():
                #  check if the col is indexed 
                if col_name in row:
                    col_value = row[col_name]

                    # make sure if this value is not indexed, initialize an empty list
                    if col_value not in index_dict:
                        index_dict[col_value] = []

                    index_dict[col_value].append(row)


            return row
        
    def select(self, columns: list[str], where: Dict[str, Any]):
        condition_cols = set(where.keys())
        for col in condition_cols:
            if col not in self.columns_set:
                raise ValueError(f"Column '{col}' does not exist in this table")

        candidate_rows = None

        # Index scan
        for col, conditions in where.items():
            if col in self.indexes:
                if not isinstance(conditions, list):
                    conditions = [conditions]

                for condition in conditions:
                    if isinstance(condition, dict):
                        operator = condition.get("operator", "=")
                        target_value = condition.get("value")
                    else:
                        operator = "="
                        target_value = condition

                    # Hash indexes only support equality
                    if operator == "=":
                        index_dict = self.indexes[col]
                        
                        # This now returns a list of rows (or None)
                        found_rows = index_dict.get(target_value) 
                        
                        if found_rows is not None:
                            # Found a subset of rows using this index!
                            candidate_rows = found_rows
                        else:
                            # Index used, but zero rows match
                            candidate_rows = [] 
                            
                        break # Stop checking conditions for this column
                        
                if candidate_rows is not None:
                    break # grabbed a subset using ONE index, stop looking at other indexes!

        # Sequential scan
        if candidate_rows is None:
            candidate_rows = self.rows

        # filter and yield 
        # We loop through either the small index list OR the full table
        for row in candidate_rows:
            # row_matches_where will verify the REST of the WHERE conditions
            if self.row_matches_where(row, where):
                yield {col: row.get(col) for col in columns}

    def row_matches_where(self, row: Dict[str, Any], where: Dict[str, Any]) -> bool:
        for col, conditions in where.items():
            # col = col_name
            # conditions = [{operator:"", value:Any}] example :{age: [{ooperator:6, value:6}, {operator :">", value:10}]}
            if not isinstance(conditions, list):
                conditions = [conditions]

            for condition in conditions:
                row_value = row.get(col)

                if isinstance(condition, dict):
                    operator = condition.get("operator", "=")
                    target_value = condition.get("value")
                else:
                    operator = "="
                    target_value = condition

                if operator == "=" and not (row_value == target_value):
                    return False
                elif operator == ">" and not (row_value > target_value):
                    return False
                elif operator == "<" and not (row_value < target_value):
                    return False
                elif operator == ">=" and not (row_value >= target_value):
                    return False
                elif operator == "<=" and not (row_value <= target_value):
                    return False
                elif operator in ("!=", "<>") and not (row_value != target_value):
                    return False
                
        return True

