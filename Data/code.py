import duckdb
db_path = "RELIANCE_EQ.db"
conn = duckdb.connect(db_path)
print("=== TABLE STRUCTURE ===")
result = conn.execute("PRAGMA table_info(stock_data)")
columns = result.fetchall()
for col in columns:
    print(f"Column: {col[1]}, Type: {col[2]}")
print("\n=== SAMPLE DATA ===")
result = conn.execute("SELECT * FROM stock_data LIMIT 50")
sample = result.fetchall()
for row in sample:
    print(row)
conn.close()