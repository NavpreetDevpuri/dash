from celery import Celery
from celery.events import EventReceiver
from kombu import Connection
from celery_arangodb import multiply, notify  # Import dependent tasks
from arango import ArangoClient

# Celery Configuration
app = Celery(
    "celery_arangodb",
    broker="redis://localhost:6379/0",
    backend="arangodb://root:zxcv@localhost:8529/celery_results/celery_taskmeta"
)

# ArangoDB Credentials
ARANGO_URL = "http://localhost:8529"
ARANGO_USER = "root"
ARANGO_PASSWORD = "zxcv"
ARANGO_DB_NAME = "celery_results"
ARANGO_COLLECTION_NAME = "celery_taskmeta"

# Connect to ArangoDB
client = ArangoClient()
db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
tasks_collection = db.collection(ARANGO_COLLECTION_NAME)

def is_task_processed(task_id):
    """Check if the task has already been processed to avoid loops."""
    task = tasks_collection.get(task_id)
    return task and "processed" in task

def mark_task_as_processed(task_id):
    """Mark a task as processed in ArangoDB to prevent re-triggering."""
    tasks_collection.update({"_key": task_id, "processed": True})

def task_completed(event):
    """Handle Celery task completion events."""
    task_id = event["uuid"]
    result = event.get("result")

    # Check if task has already been processed
    if is_task_processed(task_id):
        print(f"🔁 Task {task_id} already processed, skipping...")
        return

    print(f"✅ Task {task_id} completed with result: {result}")

    # 🛑 Check if result is None
    if result is None:
        print(f"⚠️ Task {task_id} returned None. Skipping next steps.")
        mark_task_as_processed(task_id)  # Mark as processed
        return  # Exit early

    try:
        # 🚀 Trigger the next task only if result is a valid number
        next_task = multiply.delay(int(result))
        notify.delay(f"Triggered multiply task: {next_task.id}")

        # ✅ Mark task as processed in ArangoDB
        mark_task_as_processed(task_id)

    except ValueError:
        print(f"❌ Error: Task {task_id} returned invalid result '{result}', skipping.")

def monitor_events():
    """Listen for Celery task events."""
    print("🔍 Listening for task events...")
    with Connection(app.conf.broker_url) as conn:
        recv = EventReceiver(conn, handlers={"task-succeeded": task_completed})
        recv.capture(limit=None, timeout=None, wakeup=True)

if __name__ == "__main__":
    monitor_events()