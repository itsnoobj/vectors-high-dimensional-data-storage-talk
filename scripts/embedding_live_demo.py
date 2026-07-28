#!/usr/bin/env python3
"""Demystifying AI — see real embeddings generated for any sentence."""
import warnings
import os
import numpy as np

warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from sentence_transformers import SentenceTransformer

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def display_embedding(sentence, embedding):
    """Show a sentence and its first few embedding dimensions."""
    print(f'\n  "{BOLD}{sentence}{RESET}"')
    preview = ", ".join(f"{v:.4f}" for v in embedding[:8])
    print(f"  → [{GREEN}{preview}{RESET}, ... ×{len(embedding)} dims]")


def main():
    print(f"\n{'=' * 60}")
    print(f"  {CYAN}{BOLD}EMBEDDINGS: Text → Numbers (real model){RESET}")
    print(f"{'=' * 60}")
    print(f"  {DIM}Model: all-MiniLM-L6-v2 (384 dimensions){RESET}")
    print(f"  {DIM}Loading...{RESET}", end="", flush=True)

    model = SentenceTransformer("all-MiniLM-L6-v2")
    print(" done.\n")

    defaults = [
        "I love french fries",
        "Fries are delicious",
        "The stock market crashed",
    ]

    # Show defaults
    embeddings = model.encode(defaults)
    print(f"{YELLOW}── Same meaning = similar numbers ──{RESET}")
    for sent, emb in zip(defaults, embeddings):
        display_embedding(sent, emb)

    # Show cosine between first two vs first and third
    cos_similar = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    cos_different = np.dot(embeddings[0], embeddings[2]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[2])
    )
    print(f"\n  {DIM}cosine(fries, delicious) = {GREEN}{cos_similar:.3f}{RESET}")
    print(f"  {DIM}cosine(fries, stock market) = {CYAN}{cos_different:.3f}{RESET}")

    # User input
    print(f"\n{'─' * 60}")
    user = input(f"  {BOLD}Type a sentence (Enter to skip):{RESET} ").strip()
    if user:
        emb = model.encode([user])[0]
        display_embedding(user, emb)
        print(f"  {DIM}That's {len(emb)} numbers representing its meaning.{RESET}")

    print(f"\n{'=' * 60}")
    print(f"  {BOLD}Each sentence → {GREEN}384 numbers{RESET}.")
    print(f"  Now imagine doing this for 500 words × 96 layers...")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
