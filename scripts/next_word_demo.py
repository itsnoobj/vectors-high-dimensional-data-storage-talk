#!/usr/bin/env python3
"""Demystifying AI — next-word prediction & how temperature steers it."""
import math
import random
import time

C = "\033[96m"; G = "\033[92m"; Y = "\033[93m"; D = "\033[2m"; B = "\033[1m"; R = "\033[0m"

PROMPT = "The capital of France is"

# Hardcoded "logits" — raw scores the model would produce for next words.
WORDS = ["Paris", "Lyon", "located", "famous", "Marseille", "home"]
LOGITS = [6.0, 2.5, 2.0, 1.5, 1.2, 1.0]


def softmax(logits, temperature):
    if temperature <= 0:  # greedy: all mass on the top word
        top = logits.index(max(logits))
        return [1.0 if i == top else 0.0 for i in range(len(logits))]
    z = [x / temperature for x in logits]
    m = max(z)
    e = [math.exp(v - m) for v in z]
    s = sum(e)
    return [v / s for v in e]


def weighted_choice(rng, words, probs):
    r = rng.random()
    acc = 0.0
    for w, p in zip(words, probs):
        acc += p
        if r <= acc:
            return w
    return words[-1]


def bar_chart(probs):
    top = max(probs)
    for w, p in sorted(zip(WORDS, probs), key=lambda x: -x[1]):
        blocks = "█" * int(round(p * 30))
        col = G if p == top else C
        print(f"    {w:<11}{col}{blocks}{R} {D}{p * 100:5.1f}%{R}")
        time.sleep(0.15)


def main():
    print("=" * 60)
    print(f"  {C}{B}NEXT-WORD PREDICTION: It's Just Probabilities{R}")
    print("=" * 60)
    print(f'\n  Prompt: "{B}{PROMPT}{R} ___"\n')
    time.sleep(0.8)

    for temp in (0.0, 0.7, 1.5):
        label = "greedy" if temp == 0 else ("balanced" if temp < 1 else "creative")
        print(f"{Y}── temperature = {temp}  ({label}) ──{R}")
        bar_chart(softmax(LOGITS, temp))
        print()
        time.sleep(0.6)

    print("─" * 60)
    print(f"  {B}Sampling 5 times at each temperature:{R}\n")
    rng = random.Random(42)
    for temp in (0.0, 0.7, 1.5):
        probs = softmax(LOGITS, temp)
        picks = [weighted_choice(rng, WORDS, probs) for _ in range(5)]
        print(f"  temp {temp:<4} → {G}{', '.join(picks)}{R}")
        time.sleep(0.6)

    print("=" * 60)
    print(f"  {D}temp=0  → deterministic, always the top token{R}")
    print(f"  {D}temp↑   → flatter distribution, more variety (and risk){R}")
    print("=" * 60)


if __name__ == "__main__":
    main()
