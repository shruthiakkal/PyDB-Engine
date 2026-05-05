from typing import Any

from src.enums.table_enums import QueryEnum
from src.parser.ast import DeleteStatement, InsertStatement, SelectStatement




class SqlParser:
    def tokenize(self, data: str) -> list[str]:
        data = data.replace("(", " ")
        data = data.replace(")", " ")
        data = data.replace(",", " ")
        data = data.replace(";", " ")
        data = data.replace("=", " ")
        return data.split()

    def clean_token(self, token: str) -> str:
        return token.strip().strip("'").strip('"').lower()

    def parse(self, data: str | None) -> InsertStatement | SelectStatement | None:
        if not data:
            return None
        
        if data[-1] != ";":
            return None

        tokens = self.tokenize(data)

        if len(tokens) < 2:
            return None

        query_type = tokens[0].upper()

        if query_type not in {
            QueryEnum.INSERT,
            QueryEnum.SELECT,
            QueryEnum.DELETE,
        }:
            return None

        if query_type == QueryEnum.INSERT:
            return self.parse_insert(tokens)

        if query_type == QueryEnum.SELECT:
            return self.parse_select(tokens)

        if query_type == QueryEnum.DELETE:
            return self.parse_delete(tokens)

        return None

    def parse_insert(self, tokens: list[str]) -> InsertStatement | None:
        # INSERT INTO drivers first_name last_name VALUES John Doe

        if len(tokens) < 6:
            return None

        if tokens[1].upper() != QueryEnum.INTO:
            return None

        table = self.clean_token(tokens[2])

        try:
            values_index = [token.upper() for token in tokens].index(QueryEnum.VALUES)
        except ValueError:
            return None

        columns = [self.clean_token(token) for token in tokens[3:values_index]]
        values = [self.clean_token(token) for token in tokens[values_index + 1:]]

        if len(columns) != len(values):
            return None

        return InsertStatement(table, columns, values)

    def parse_select(self, tokens: list[str]) -> SelectStatement | None:
        # SELECT first_name last_name FROM drivers
        # SELECT * FROM drivers

        try:
            from_index = [token.upper() for token in tokens].index(QueryEnum.FROM)
        except ValueError:
            return None

        columns = [self.clean_token(token) for token in tokens[1:from_index]]

        if from_index + 1 >= len(tokens):
            return None

        table = self.clean_token(tokens[from_index + 1])

        return SelectStatement(table, columns)

    def parse_delete(self, tokens: list[str]) ->DeleteStatement | None:
        # DELETE FROM drivers WHERE id abc123

        if len(tokens) < 6:
            return None

        if tokens[1].upper() != QueryEnum.FROM:
            return None

        table = self.clean_token(tokens[2])

        if tokens[3].upper() != QueryEnum.WHERE:
            return None

        column = self.clean_token(tokens[4])
        value = self.clean_token(tokens[5])

        return DeleteStatement(type, column, value)
        