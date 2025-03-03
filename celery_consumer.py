import time
from celery.result import AsyncResult
from celery_arangodb import app, multiply, notify
from arango import ArangoClient

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

def get_pending_tasks():
    """Fetch all tasks that have not been processed yet."""
    query = f"""
    FOR doc IN {ARANGO_COLLECTION_NAME}
        FILTER doc.state == 'SUCCESS' && !HAS(doc, 'processed')
        RETURN doc
    """
    return list(db.aql.execute(query))

def mark_task_as_processed(task_id):
    """Mark a task as processed to avoid duplicate execution."""
    tasks_collection.update({"_key": task_id, "processed": True})

def monitor_tasks():
    """Continuously monitor completed tasks and trigger follow-up tasks."""
    print("🔍 Monitoring for completed tasks...")

    while True:
        completed_tasks = get_pending_tasks()

        for task in completed_tasks:
            task_id = task["_key"]
            result_value = task["result"]

            print(f"✅ Task {task_id} completed with result: {result_value}")
            print("🚀 Triggering multiply task...")
            next_task = multiply.delay(int(result_value))  # Convert to int if needed

            notify.delay(f"Triggered multiply task: {next_task.id}")

            # Mark as processed in ArangoDB to prevent reprocessing
            mark_task_as_processed(task_id)

        time.sleep(5)  # Wait before checking again

if __name__ == "__main__":
    monitor_tasks()