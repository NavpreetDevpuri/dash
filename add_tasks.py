from celery_arangodb import add

print("🚀 Enqueueing tasks...")
task1 = add.delay(10, 20)
task2 = add.delay(30, 40)
task3 = add.delay(50, 60)

print(f"📌 Task IDs: {task1.id}, {task2.id}, {task3.id}")