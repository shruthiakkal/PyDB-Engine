import threading

from src.engine.executor import PyDBEngine
from src.parser.ast import InsertStatement

# Test healthy case - insert
def test_engine_executes_insert():
    db = PyDBEngine()
    db.execute_ddl("users", ["id", "name"])

    ast = InsertStatement(
        table_name="users", 
        columns=["id", "name"], 
        values=[1, "Bob"]
    )

    db.execute(ast)

    assert len(db.tables["users"].rows) == 1
    assert db.tables["users"].rows[0] == {"id": 1, "name": "Bob"}


# test - multi threading 
def test_engine_handles_concurrent_inserts():
    db = PyDBEngine()
    db.execute_ddl("logs", ["log_id", "message"])
    
    # This is the function each thread will run
    def worker(thread_id: int):
        ast = InsertStatement(
            table_name="logs", 
            columns=["log_id", "message"], 
            values=[thread_id, f"Message {thread_id}"]
        )
        # Because we share the 'db' instance across threads, 
        # the Table.lock prevents memory corruption here
        db.execute(ast)

    threads = []
    
    # Spawn 100 parallel threads
    for i in range(100):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    # Wait for all 100 threads to finish
    for t in threads:
        t.join()

    # If the lock works, we should have exactly 100 rows, with no data loss.
    assert len(db.tables["logs"].rows) == 100
