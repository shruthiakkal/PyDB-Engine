from typing import Any, Dict, List

from src.parser.ast import InsertStatement
from src.storage.table import Table


class PyDBEngine:
    def __init__(self):
        # The database holds a collection of tables in memory
        self.tables: Dict[str, Table] = {}

    def execute_ddl(self, table_name: str, columns: List[str]):
        """Data Definition Language (CREATE TABLE)"""
        self.tables[table_name] = Table(table_name, columns)

    def execute(self, statement: Any):
        """INSERT, SELECT """
        
        if isinstance(statement, InsertStatement):
            table = self.tables.get(statement.table_name)
            if not table:
                raise ValueError(f"Table '{statement.table_name}' does not exist.")
            
            # write to the specific Table object
            return table.insert(statement.columns, statement.values)
        
        else:
            raise NotImplementedError("Only INSERT is supported now.")