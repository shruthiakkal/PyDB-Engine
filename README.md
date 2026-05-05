# PyDB-Engine

## Architecture of PyDB Engine

### The SQL Parser

Before the database can do anything, it needs to understand text. Do not use regex to parse SQL.

- Convert a string like SELECT id FROM users; into tokens: [KEYWORD: SELECT], [IDENTIFIER: id], [KEYWORD: FROM], [IDENTIFIER: users].
- Convert those tokens into an Abstract Syntax Tree (AST). You can write a hand-rolled Recursive Descent Parser.
- Once you have an AST, your engine needs to decide how to execute it. If it's a SELECT with a WHERE clause, the planner checks if an index exists for that column.
- Support only CREATE TABLE, INSERT, SELECT, and DELETE with basic WHERE clauses.
