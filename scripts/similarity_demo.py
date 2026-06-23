#!/usr/bin/env python3
"""Demystifying AI — cosine similarity with hand-crafted 8-dim 'embeddings'."""
import math
import time

C = "\033[96m"; G = "\033[92m"; Y = "\033[93m"; RED = "\033[91m"; D = "\033[2m"; B = "\033[1m"; R = "\033[0m"

# Fake but intuitive 8-dim embeddings. Dimensions loosely mean:
# [business, churn/loss, users, subscription, food, cooking, recipe, leisure]
EMB = {
    "customer churn":                  [0.9, 0.9, 0.7, 0.6, 0.0, 0.0, 0.0, 0.1],
    "users cancelling subscriptions":  [0.8, 0.8, 0.9, 0.9, 0.0, 0.0, 0.0, 0.1],
    "french fries recipe":             [0.0, 0.0, 0.1, 0.0, 0.9, 0.9, 0.9, 0.4],
}


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(a):
    return math.sqrt(sum(x * x for x in a))


def cosine(a, b):
    return dot(a, b) / (norm(a) * norm(b))


def euclidean(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def main():
    print("=" * 64)
    print(f"  {C}{B}COSINE SIMILARITY: Measuring Meaning{R}")
    print("=" * 64)
    print(f"\n  {D}Each sentence is a vector. Closer vectors = closer meaning.{R}\n")
    time.sleep(0.8)

    for text, vec in EMB.items():
        nums = ", ".join(f"{v:.1f}" for v in vec)
        print(f'  {B}{text:<32}{R} {D}[{nums}]{R}')
        time.sleep(0.5)

    query = "customer churn"
    qv = EMB[query]
    print(f"\n{'─' * 64}")
    print(f"  Comparing against: {Y}\"{query}\"{R}\n")
    time.sleep(0.6)

    print(f"  {B}{'sentence':<34}{'cosine':>9}{'euclid':>9}{R}")
    print(f"  {D}{'-' * 52}{R}")
    for text, vec in EMB.items():
        if text == query:
            continue
        cs = cosine(qv, vec)
        eu = euclidean(qv, vec)
        bar = "█" * int(cs * 20)
        col = G if cs > 0.5 else RED
        verdict = "similar" if cs > 0.5 else "unrelated"
        print(f"  {text:<34}{col}{cs:>9.2f}{R}{eu:>9.2f}  {col}{bar}{R} {D}{verdict}{R}")
        time.sleep(0.7)

    print("=" * 64)
    print(f"  {G}High cosine{R} → same idea (churn ≈ cancelling subscriptions)")
    print(f"  {RED}Low cosine{R}  → different topic (churn ≠ fries recipe)")
    print(f"  {D}Note: cosine cares about direction; euclidean about distance.{R}")
    print("=" * 64)


if __name__ == "__main__":
    main()
