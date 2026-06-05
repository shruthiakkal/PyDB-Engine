from src.engine.executor import PyDBEngine
from src.parser.parser import SqlParser


if __name__ == "__main__":
    db = PyDBEngine()

    db.execute_ddl("drivers", ["first_name", "last_name"])
    print("PyDB Engine started. Type SQL or 'exit' to quit.")

    while True:
        query = input("pydb> ")
        if query.lower() == "exit":
            break

        try:
            parser = SqlParser()
            ast = parser.parse(query)
            result = db.execute(ast)
            print(result)

        except Exception as e:
            print(f"Error: {e}")
