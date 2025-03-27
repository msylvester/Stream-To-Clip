# celeryconfig.py
# This file contains configuration settings for Celery workers
# Save this in the same directory as server.py

# Broker settings (Redis)
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'

# Task serialization
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'

# Task execution settings
task_time_limit = 3600  # 1 hour max runtime for tasks
task_soft_time_limit = 3300  # Soft limit 55 minutes (gives tasks time to clean up)
worker_prefetch_multiplier = 1  # Only prefetch one task at a time (good for long tasks)
worker_max_tasks_per_child = 10  # Restart worker after 10 tasks to prevent memory leaks

# Log settings
worker_hijack_root_logger = False
worker_log_color = True

# Task result settings
task_ignore_result = False
result_expires = 86400  # Results expire after 1 day

# Concurrency
# If processing video is CPU intensive, set this to match your CPU cores
# worker_concurrency = 4  # Uncomment and set to number of available CPU cores
