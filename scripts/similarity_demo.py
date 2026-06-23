#!/usr/bin/env python3
"""Demystifying AI — interactive cosine similarity with hand-crafted 'embeddings'.

SIMULATION ONLY: embeddings are hardcoded, not produced by a real model.
"""
import difflib
import time

import numpy as np

C = "\033[96m"; G = "\033[92m"; Y = "\033[93m"; RED = "\033[91m"; D = "\033[2m"; B = "\033[1m"; R = "\033[0m"

# Fake but intuitive 8-dim embeddings. Dimensions loosely mean:
# [business, churn/loss, users, subscription, food, cooking, leisure, tech]
EMB = {
    "customer churn":                  [0.90, 0.90, 0.70, 0.60, 0.00, 0.00, 0.10, 0.10],
    "users cancelling subscriptions":  [0.80, 0.80, 0.90, 0.95, 0.00, 0.00, 0.10, 0.10],
    "subscription revenue growth":     [0.90, 0.10, 0.60, 0.90, 0.00, 0.00, 0.10, 0.20],
    "how to reduce customer attrition":[0.85, 0.85, 0.70, 0.50, 0.00, 0.00, 0.10, 0.10],
    "french fries recipe":             [0.00, 0.00, 0.10, 0.00, 0.95, 0.90, 0.40, 0.00],
    "how to bake chocolate cake":      [0.00, 0.00, 0.10, 0.00, 0.90, 0.95, 0.40, 0.00],
    "best restaurants in paris":       [0.20, 0.00, 0.20, 0.00, 0.85, 0.20, 0.70, 0.00],
    "weekend hiking trip":             [0.00, 0.00, 0.20, 0.00, 0.10, 0.00, 0.95, 0.00],
    "machine learning model training": [0.30, 0.00, 0.20, 0.00, 0.00, 0.00, 0.10, 0.95],
    "database query optimization":     [0.30, 0.00, 0.20, 0.00, 0.00, 0.00, 0.05, 0.95],
}


def cosine(a, b):
    a, b = np.array(a), np.array(b)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def word_overlap(q, s):
    qw, sw = set(q.lower().split()), set(s.lower().split())
    return len(qw & sw) / len(qw | sw) if qw | sw else 0.0


def resolve(query):
    """Map free-text input to a known vocabulary entry (the simulation)."""
    keys = list(EMB)
    fuzzy = difflib.get_close_matches(query.lower(), keys, n=1, cutoff=0.6)
    if fuzzy:
        return fuzzy[0], EMB[fuzzy[0]], f"matched known sentence {Y}\"{fuzzy[0]}\"{R}"
    scored = sorted(keys, key=lambda k: word_overlap(query, k), reverse=True)
    best = scored[0]
    if word_overlap(query, best) > 0:
        return best, EMB[best], f"{Y}not in the precomputed set{R} — using nearest by word overlap: {B}\"{best}\"{R}"
    return None, None, None


def main():
    print("=" * 64)
    print(f"  {C}{B}COSINE SIMILARITY: Measuring Meaning{R}")
    print("=" * 64)
    print(f"  {D}Note: This is a simulation for illustration (hardcoded vectors).{R}\n")

    print(f"  {D}Known sentences in this demo:{R}")
    for s in EMB:
        print(f"    {D}• {s}{R}")

    raw = input(f"\n  {B}Type a sentence{R} {D}(Enter for 'customer churn'){R}: ").strip()
    query = raw or "customer churn"

    name, qv, note = resolve(query)
    if qv is None:
        print(f"\n  {RED}Hmm — \"{query}\" shares no words with any known sentence.{R}")
        print(f"  {D}Try one of the sentences listed above, or rephrase using similar words.{R}")
        return

    print(f"\n  You typed: {Y}\"{query}\"{R}")
    print(f"  {D}→ {note}{R}\n")
    time.sleep(0.5)

    print(f"  {B}{'sentence':<34}{'cosine':>9}{R}")
    print(f"  {D}{'-' * 43}{R}")
    ranked = sorted(EMB.items(), key=lambda kv: cosine(qv, kv[1]), reverse=True)
    for text, vec in ranked:
        if text == name:
            continue
        cs = cosine(qv, vec)
        bar = "█" * int(cs * 20)
        col = G if cs > 0.5 else RED
        verdict = "similar" if cs > 0.5 else "unrelated"
        print(f"  {text:<34}{col}{cs:>9.2f}{R}  {col}{bar}{R} {D}{verdict}{R}")
        time.sleep(0.25)

    print("=" * 64)
    print(f"  {G}High cosine{R} → same idea   {RED}Low cosine{R} → different topic")
    print("=" * 64)


if __name__ == "__main__":
    main()
