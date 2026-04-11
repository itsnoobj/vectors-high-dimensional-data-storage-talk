#!/usr/bin/env python3
"""Semantic search via SQL — embed a query, find closest docs."""
import os, sys, psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL', 'postgres://postgres:mysecret@localhost:5432/postgres'))
cur = conn.cursor()

model = SentenceTransformer('all-MiniLM-L6-v2')
query = sys.argv[1] if len(sys.argv) > 1 else "how to find and fix slow database queries"

emb = model.encode(query).tolist()

print(f"\n🔍 Query: \"{query}\"\n")
print(f"{'─' * 60}")
print(f"  SQL: SELECT content, embedding <=> '[query_vector]' AS distance")
print(f"       FROM docs_demo ORDER BY distance LIMIT 3;")
print(f"{'─' * 60}\n")

cur.execute("""
    SELECT content, embedding <=> %s::vector AS distance
    FROM docs_demo ORDER BY distance LIMIT 3
""", (str(emb),))

for rank, (content, dist) in enumerate(cur.fetchall(), 1):
    bar = "█" * int((1 - dist) * 30)
    print(f"  {rank}. [{1-dist:.1%}] {bar}")
    print(f"     \"{content}\"\n")

print(f"  💡 No keyword overlap needed — pure meaning match.")
conn.close()
