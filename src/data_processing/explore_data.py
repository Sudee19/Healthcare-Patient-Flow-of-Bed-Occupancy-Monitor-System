import sqlite3
import json
import pandas as pd

# Explore database structure
db_path = 'data/hospital.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"- {table[0]}")

# Get schema for each table
for table in tables:
    table_name = table[0]
    print(f"\nSchema for {table_name}:")
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Get sample data
    print(f"Sample data from {table_name}:")
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row}")

conn.close()

# Explore JSON data structure
print("\n" + "="*50)
print("Exploring JSON data structure:")

try:
    with open('data/test_events.json', 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        print(f"JSON contains {len(data)} records")
        if data:
            print("Sample record keys:", list(data[0].keys()) if isinstance(data[0], dict) else "Not a dictionary")
            print("Sample record:", data[0])
    else:
        print("JSON structure:", type(data))
        print("Keys:", list(data.keys()) if isinstance(data, dict) else "Not a dictionary")
        
except Exception as e:
    print(f"Error reading JSON: {e}")
