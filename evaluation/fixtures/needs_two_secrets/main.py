import os

db = os.environ["DB_URL"]
token = os.environ["API_TOKEN"]
print(f"connected with {len(db)} and {len(token)} characters")
