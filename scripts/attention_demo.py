#!/usr/bin/env python3
"""Demystifying AI — interactive view of where a model 'pays attention'.

SIMULATION ONLY: weights come from a simple heuristic, not a real model.
"""
import time

HI = "\033[92m"; MID = "\033[93m"; LO = "\033[2m"; C = "\033[96m"; B = "\033[1m"; R = "\033[0m"

DEFAULT = "As a QA engineer write test cases for the LOGIN page focusing on SECURITY edge cases"

# Low-signal filler words get almost no attention.
STOP = {
    "a", "an", "the", "as", "at", "by", "for", "in", "of", "on", "to", "up", "and",
    "or", "but", "is", "are", "was", "were", "be", "it", "its", "this", "that", "with",
    "i", "you", "he", "she", "we", "they", "my", "your", "from", "into", "about",
}


def score(word):
    """Heuristic attention weight in [0,1] for any token."""
    bare = "".join(ch for ch in word if ch.isalnum())
    if not bare:
        return 0.05
    if bare.isupper() and len(bare) > 1:   # SHOUTED / emphasized terms
        return 0.97
    if bare.lower() in STOP:               # articles, prepositions, pronouns
        return 0.05
    if bare[0].isupper():                  # likely proper noun
        return 0.85
    if len(bare) >= 7:                     # long content words
        return 0.80
    if len(bare) >= 5:
        return 0.60
    return 0.35


def color_for(w):
    return HI if w >= 0.7 else (MID if w >= 0.4 else LO)


def main():
    print("=" * 66)
    print(f"  {C}{B}ATTENTION: What the Model Focuses On{R}")
    print("=" * 66)
    print(f"  {LO}Note: This is a simulation for illustration (heuristic weights).{R}\n")

    raw = input(f"  {B}Type any prompt{R} {LO}(Enter for the default){R}: ").strip()
    prompt = raw or DEFAULT

    words = prompt.split()
    weights = {w: score(w) for w in words}

    rendered = " ".join(f"{color_for(weights[w])}{w}{R}" for w in words)
    print(f"\n  {rendered}\n")
    time.sleep(0.6)

    print("─" * 66)
    print(f"  {B}Attention bars{R}  ({HI}green=high{R}  {MID}yellow=medium{R}  {LO}dim=low{R})\n")
    for w in words:
        weight = weights[w]
        col = color_for(weight)
        bar = "█" * int(round(weight * 30))
        print(f"  {col}{w:<12}{bar}{R} {LO}{weight:.2f}{R}")
        time.sleep(0.15)

    print("=" * 66)
    top = sorted(set(words), key=lambda w: weights[w], reverse=True)[:4]
    print(f"  Model locks onto: {HI}{', '.join(top)}{R}")
    print(f"  {LO}Filler words (a, the, for, on) get almost no attention.{R}")
    print("=" * 66)


if __name__ == "__main__":
    main()
