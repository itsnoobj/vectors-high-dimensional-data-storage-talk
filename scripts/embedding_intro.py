#!/usr/bin/env python3
"""Quick demo: show how embeddings capture meaning, not keywords."""
import warnings; warnings.filterwarnings("ignore")
import os; os.environ["TOKENIZERS_PARALLELISM"] = "false"
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')

texts = [
    "My flight got cancelled",
    "The airline delayed my trip",
    "The stock market crashed",
]

embeddings = model.encode(texts)

print("=" * 60)
print("  EMBEDDINGS: Meaning, Not Keywords")
print("=" * 60)

for text, emb in zip(texts, embeddings):
    print(f'\n  "{text}"')
    print(f"  → [{emb[0]:+.3f}, {emb[1]:+.3f}, {emb[2]:+.3f}, {emb[3]:+.3f}, ...] ({len(emb)} dims)")

print(f"\n{'─' * 60}")
print("  Similarity (cosine):\n")
for i in range(len(texts)):
    for j in range(i + 1, len(texts)):
        score = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
        bar = "█" * int(score * 20)
        print(f'  "{texts[i]}"')
        print(f'  "{texts[j]}"')
        print(f"    → {score:.2f}  {bar}\n")
print(f"  Zero words in common. The model gets it.")
print(f"{'=' * 60}")
