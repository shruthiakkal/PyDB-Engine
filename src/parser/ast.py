from typing import Any, Dict, List


class InsertStatement:
    def __init__(self, table_name: str, columns: List[str], values: List[Any]):
        self.table_name = table_name
        self.columns = columns
        self.values = values

class SelectStatement:
    def __init__(self, table_name: str, columns: List[str], where:Dict[str, Any]):
        self.table_name = table_name
        self.columns = columns
        self.where = where

class DeleteStatement:
    def __init__(self, table_name: str, columns: List[str], values: List[Any]):
        self.table_name = table_name
        self.columns = columns
        self.values = values
