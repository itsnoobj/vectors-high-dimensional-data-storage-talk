#!/usr/bin/env python3
"""Demystifying AI — real cosine similarity using sentence-transformers."""
import numpy as np
import time
import warnings
import os

warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from sentence_transformers import SentenceTransformer

CYAN = "\033[96m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

CORPUS = [
    "customer churn is increasing this quarter",
    "users are cancelling their subscriptions",
    "french fries recipe with garlic aioli",
    "the login page has a bug on mobile",
    "authentication fails on the sign-in screen",
    "quarterly revenue report Q4 2025",
    "how to make crispy potato wedges",
    "employee onboarding process document",
    "new hire orientation checklist",
    "the bank is steep and covered in mud",
    "the bank is closed for the holiday",
]


def cosine_similarity(vec_a, vec_b):
    """Compute cosine similarity between two vectors."""
    dot = np.dot(vec_a, vec_b)
    norm = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
    return dot / norm if norm > 0 else 0.0


def display_results(query, corpus, similarities):
    """Display ranked similarity results with bars."""
    ranked = sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)
    print(f"\n  {BOLD}Results for:{RESET} \"{YELLOW}{query}{RESET}\"\n")
    for idx, score in ranked:
        bar_len = int(score * 25)
        bar = "█" * bar_len
        color = GREEN if score > 0.5 else RED if score < 0.3 else CYAN
        print(f"    {color}{score:.3f}{RESET} {color}{bar}{RESET} {corpus[idx]}")
    print()


def main():
    print(f"\n{'=' * 60}")
    print(f"  {CYAN}{BOLD}COSINE SIMILARITY: Real Embeddings{RESET}")
    print(f"{'=' * 60}")
    print(f"  {DIM}Model: all-MiniLM-L6-v2 (384 dimensions){RESET}")
    print(f"  {DIM}Loading model...{RESET}", end="", flush=True)

    model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f" done.\n")

    # Encode corpus
    corpus_embeddings = model.encode(CORPUS)

    # Show corpus
    print(f"  {BOLD}Corpus ({len(CORPUS)} sentences):{RESET}")
    for sentence in CORPUS:
        print(f"    • {sentence}")

    # Get query
    print(f"\n{'─' * 60}")
    query = input(f"  {BOLD}Type a query (Enter for default):{RESET} ").strip()
    if not query:
        query = "users are leaving the platform"

    # Encode and compare
    query_embedding = model.encode([query])[0]
    similarities = [cosine_similarity(query_embedding, emb) for emb in corpus_embeddings]

    display_results(query, CORPUS, similarities)

    # Show embedding snippet
    print(f"  {DIM}Embedding for \"{query[:30]}...\":{RESET}")
    print(f"  {DIM}[{query_embedding[0]:.4f}, {query_embedding[1]:.4f}, {query_embedding[2]:.4f}, ... ×384 dims]{RESET}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
