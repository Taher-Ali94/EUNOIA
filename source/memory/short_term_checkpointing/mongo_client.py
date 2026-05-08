from functools import wraps
from langgraph.checkpoint.mongodb import MongoDBSaver


def with_mongo_checkpointer(uri: str = "mongodb://localhost:27017", db_name: str = "Eunoia_Memories", thread_id: str = "default_thread"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                with MongoDBSaver.from_conn_string(uri, db_name) as checkpointer:
                    config = {
                        "configurable": {
                            "thread_id": thread_id
                        }
                    }
                    return func(*args, checkpointer=checkpointer, config=config, **kwargs)
            except Exception as e:
                print(f"Error in MongoDB checkpointer: {e}")
                raise
        return wrapper
    return decorator

"""
Usage

@with_mongo_checkpointer(
    uri="mongodb://localhost:27017",
    db_name="juicy",
    thread_id="taher-session"
)
def run_agent(checkpointer, config):
    app = graph_builder.compile(checkpointer=checkpointer)

    while True:
        user_input = input('User: ')
        if user_input.lower() in ("exit", "quit"):
            break
        app.invoke(
            {
                "step": "START",
                "content": user_input,
                "tool": None,
                "tool_input": None,
                "role": "user",
                "messages": [{"role": "user", "content": user_input}],
            },
            config=config,
        )

run_agent()

"""