#!/usr/bin/env python3
"""Embed a sentence and print the vector — ready to paste into SQL."""
import sys
from sentence_transformers import SentenceTransformer

query = sys.argv[1] if len(sys.argv) > 1 else "how to find and fix slow queries"
model = SentenceTransformer('all-MiniLM-L6-v2')
emb = model.encode(query)

print(f"\n🔍 \"{query}\"\n")
print(f"📐 Vector ({len(emb)} dims, first 5): [{', '.join(f'{v:.4f}' for v in emb[:5])}, ...]")
print(f"\n📋 Copy-paste for SQL:\n")
print(f"'[{','.join(f'{float(v):.8f}' for v in emb)}]'")
