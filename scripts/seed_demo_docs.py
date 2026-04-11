#!/usr/bin/env python3
"""Seed 10 docs into pgvector for the semantic search demo."""
import os, psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL', 'postgres://postgres:mysecret@localhost:5432/postgres'))
cur = conn.cursor()

cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
cur.execute("DROP TABLE IF EXISTS docs_demo;")
cur.execute("CREATE TABLE docs_demo (id serial PRIMARY KEY, content text, embedding vector(384));")
conn.commit()

docs = [
    "PostgreSQL supports JSONB for storing semi-structured data",
    "The VACUUM process reclaims storage from dead tuples",
    "Connection pooling with PgBouncer reduces overhead",
    "Write-ahead logging ensures crash recovery",
    "Indexes speed up reads but slow down writes",
    "Partitioning large tables improves query performance",
    "The query planner chooses the best execution strategy",
    "Foreign keys enforce referential integrity between tables",
    "MVCC allows concurrent reads without blocking writes",
    "pg_stat_statements tracks slow queries for optimization",
]

model = SentenceTransformer('all-MiniLM-L6-v2')
for doc in docs:
    emb = model.encode(doc)
    cur.execute("INSERT INTO docs_demo (content, embedding) VALUES (%s, %s)", (doc, emb.tolist()))

conn.commit()
conn.close()
print(f"✅ Seeded {len(docs)} docs into docs_demo")
