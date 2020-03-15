import pandas as pd
import sqlite3

conn = sqlite3.connect("tiki_products.db")
df = pd.read_sql_query("SELECT * FROM products LIMIT 100;", conn)
print(df.to_string())