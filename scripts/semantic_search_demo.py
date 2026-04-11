#!/usr/bin/env python3
"""Demo: embed 10 sentences, search by meaning, show truncated vectors."""
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- 1. Load model ---
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

# --- 2. Our tiny knowledge base ---
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

# --- 3. Embed all docs ---
def embed(model, texts):
    return model.encode(texts)

# --- 4. Search: find closest docs to a query ---
def search(query_vec, doc_vecs, top_k=3):
    scores = cosine_similarity([query_vec], doc_vecs)[0]
    ranked = np.argsort(scores)[::-1][:top_k]
    return [(i, scores[i]) for i in ranked]

# --- 5. Show a truncated vector ---
def show_vector(vec, n=5):
    nums = ", ".join(f"{v:+.4f}" for v in vec[:n])
    return f"[{nums}, ... {len(vec)} dims]"

# --- Run ---
print("=" * 60)
print("  SEMANTIC SEARCH: Embed → Store → Search")
print("=" * 60)

model = load_model()
doc_vecs = embed(model, docs)

# Show what vectors look like
print(f"\n📦 Embedded {len(docs)} docs into {doc_vecs.shape[1]}d vectors:\n")
for i, (doc, vec) in enumerate(zip(docs, doc_vecs)):
    print(f"  [{i}] \"{doc[:50]}...\"")
    print(f"       → {show_vector(vec)}\n")

# Search
query = "how to find and fix slow database queries"
print(f"{'─' * 60}")
print(f"\n🔍 Query: \"{query}\"\n")

query_vec = embed(model, [query])[0]
print(f"   Query vector: {show_vector(query_vec)}\n")

results = search(query_vec, doc_vecs)
print(f"   Top {len(results)} matches:\n")
for rank, (idx, score) in enumerate(results, 1):
    bar = "█" * int(score * 30)
    print(f"   {rank}. [{score:.3f}] {bar}")
    print(f"      \"{docs[idx]}\"\n")

print(f"  💡 No keyword overlap needed — pure meaning match.")
print(f"{'=' * 60}")
