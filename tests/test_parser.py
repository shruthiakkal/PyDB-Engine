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
        # Because we share the db instance across threads, the Table.lock prevents memory corruption here
        db.execute(ast)

    threads = []
    """
    for i in range(100):
        worker(i) 
    # if you do this The program: "Execute worker(0). Wait. Done? Okay, now execute worker(1). Wait...etc untill the worker(99)"
    # The Main Thread: Is completely occupied. It cannot do anything else until all 100 workers are finished. If this were a web server, the server would be "frozen" and unable to accept new requests while this loop runs.
    """
    
    """
    # Spawn 100 parallel threads - Multithreaded (Non-Blocking Spawn)
    #  this tells OS to spwan a thread for worker(0)- moves on and says the OS to spawn a thread for worker(1) and so on....
    # The Main Thread: Is acts like a manager. It delegates the work to 100 different threads and finishes the loop in a split second. It is then free to do other things like respond to a user while the threads work in the background.
    """
   
    for i in range(100):
        # spawn and start the worker 
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start() # This means the loop finishes almost instantly

    # Wait for all 100 threads to finish
    for t in threads:
        t.join() # t.join() is where the main thread finally stops and waits. main thread cannot move past this line until Thread X is 100% finished
        # Without join(): The main thread would hit your assert statement while the 100 threads are still halfway through their insert commands. The test would fail because the database would show 0 or 5 rows instead of 100.

    '''
    Yes, the main thread os blocked but:
    The join() loop finishes almost instantly because the threads are already done with the jobs. 

    For 
    for i in range(100):
        worker(i) # Blocks for 1 second
    Total wait time for the Main Thread: 100 seconds.

    But using threads: After 1 second, all 100 workers finish their jobs simultaneously.

    You use it when the main thread cannot proceed without the data from those threads.

    If you want the main thread to never wait, you just don't use join()
    '''

    # If the lock works, we should have exactly 100 rows, with no data loss.
    assert len(db.tables["logs"].rows) == 100 
