#!/usr/bin/env python3
"""Demystifying AI — visualize where a model 'pays attention' in a prompt."""
import time

# ANSI
HI = "\033[92m"; MID = "\033[93m"; LO = "\033[2m"; C = "\033[96m"; B = "\033[1m"; R = "\033[0m"

PROMPT = "As a QA engineer write test cases for the LOGIN page focusing on SECURITY edge cases"

# Hardcoded attention weights (0..1). Meaningful words score high; filler low.
WEIGHTS = {
    "As": 0.05, "a": 0.03, "QA": 0.80, "engineer": 0.75, "write": 0.55,
    "test": 0.85, "cases": 0.70, "for": 0.05, "the": 0.03, "LOGIN": 0.95,
    "page": 0.60, "focusing": 0.30, "on": 0.04, "SECURITY": 0.98,
    "edge": 0.78, "cases": 0.70,
}


def color_for(w):
    if w >= 0.7:
        return HI
    if w >= 0.4:
        return MID
    return LO


def main():
    print("=" * 66)
    print(f"  {C}{B}ATTENTION: What the Model Focuses On{R}")
    print("=" * 66)
    print(f"\n  {LO}Not all words matter equally. Attention weights them.{R}\n")
    time.sleep(0.8)

    words = PROMPT.split()
    # Inline highlighted sentence
    rendered = " ".join(f"{color_for(WEIGHTS.get(w, 0.1))}{w}{R}" for w in words)
    print(f"  {rendered}\n")
    time.sleep(1.0)

    print("─" * 66)
    print(f"  {B}Attention bars{R}  ({HI}green=high{R}  {MID}yellow=medium{R}  {LO}dim=low{R})\n")
    for w in words:
        weight = WEIGHTS.get(w, 0.1)
        col = color_for(weight)
        bar = "█" * int(round(weight * 30))
        print(f"  {col}{w:<10}{bar}{R} {LO}{weight:.2f}{R}")
        time.sleep(0.2)

    print("=" * 66)
    top = sorted(words, key=lambda w: WEIGHTS.get(w, 0.1), reverse=True)[:4]
    print(f"  Model locks onto: {HI}{', '.join(top)}{R}")
    print(f"  {LO}Filler words (a, the, for, on) get almost no attention.{R}")
    print("=" * 66)


if __name__ == "__main__":
    main()
