import secrets
import threading
from typing import Any, Dict, List
from datetime import datetime, timezone


class Table:
    def __init__(self, name: str, columns:List[str])-> None:
        self.name = name
        self.columns = columns
        
        # In-memory storage. A list of dictionaries representing rows.
        # TODO upgrade this to a B-Tree for indexing

        self.rows:List[Dict[str, Any]] = []

        # CONCURRENCY
        # we won't `asyncio`, we are going to use threads, we MUST lock the table before writing to prevent memory corruption if two multiple requests try to insert at the exact same millisecond
        self.lock = threading.Lock()

    def insert(self, columns: List[str], values: List[Any])-> Dict[str, Any]:
        if len(columns) != len(values):
            raise ValueError("Column count does not match value count")
        
        row = dict(zip(columns, values))

        # Acquire the lock. If another thread is currently writing to this 
        # table, this thread will pause (context switch) and wait here.
        with self.lock:
            self.rows.append(row)
            return row


