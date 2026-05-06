from typing import Any, Dict


class InsertStatement:
    def __init__(self, table_name: str, columns: list[str], values: list[Any]):
        self.table_name = table_name
        self.columns = columns
        self.values = values

class SelectStatement:
    def __init__(self, table_name: str, columns: list[str], where:Dict[str, Any]):
        self.table_name = table_name
        self.columns = columns
        self.where = where

class DeleteStatement:
    def __init__(self, table_name: str, columns: list[str], values: list[Any]):
        self.table_name = table_name
        self.columns = columns
        self.values = values
