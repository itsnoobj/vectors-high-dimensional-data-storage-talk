#!/usr/bin/env python3
"""Demystifying AI — interactive next-word prediction & how temperature steers it.

SIMULATION ONLY: probability distributions are hardcoded, not from a real model.
"""
import difflib
import math
import random
import time

C = "\033[96m"; G = "\033[92m"; Y = "\033[93m"; D = "\033[2m"; B = "\033[1m"; R = "\033[0m"

# ~5 pre-built prompts → (next words, raw "logits").
PROMPTS = {
    "the capital of france is": (["Paris", "Lyon", "located", "famous", "Marseille", "home"],
                                 [6.0, 2.5, 2.0, 1.5, 1.2, 1.0]),
    "once upon a":              (["time", "midnight", "dream", "while", "star", "hill"],
                                 [6.5, 2.0, 1.8, 2.2, 1.0, 0.8]),
    "the weather today is":     (["sunny", "cloudy", "cold", "warm", "rainy", "nice"],
                                 [4.0, 3.5, 3.0, 2.8, 2.5, 2.2]),
    "i love to":                (["code", "travel", "eat", "read", "sing", "learn"],
                                 [3.8, 3.5, 3.2, 3.0, 2.0, 2.6]),
    "machine learning is":      (["powerful", "hard", "fun", "everywhere", "math", "magic"],
                                 [4.2, 3.0, 2.8, 2.5, 2.2, 1.5]),
}
GENERIC = (["the", "a", "and", "to", "of", "that"], [3.0, 2.8, 2.6, 2.4, 2.2, 2.0])


def softmax(logits, temperature):
    if temperature <= 0:
        top = logits.index(max(logits))
        return [1.0 if i == top else 0.0 for i in range(len(logits))]
    z = [x / temperature for x in logits]
    m = max(z)
    e = [math.exp(v - m) for v in z]
    s = sum(e)
    return [v / s for v in e]


def weighted_choice(rng, words, probs):
    r, acc = rng.random(), 0.0
    for w, p in zip(words, probs):
        acc += p
        if r <= acc:
            return w
    return words[-1]


def bar_chart(words, probs):
    top = max(probs)
    for w, p in sorted(zip(words, probs), key=lambda x: -x[1]):
        blocks = "█" * int(round(p * 30))
        col = G if p == top else C
        print(f"    {w:<11}{col}{blocks}{R} {D}{p * 100:5.1f}%{R}")
        time.sleep(0.12)


def main():
    print("=" * 60)
    print(f"  {C}{B}NEXT-WORD PREDICTION: It's Just Probabilities{R}")
    print("=" * 60)
    print(f"  {D}Note: This is a simulation for illustration (hardcoded logits).{R}\n")
    print(f"  {D}Known prompts:{R} " + f"{D}|{R} ".join(f'"{p}"' for p in PROMPTS))

    raw = input(f"\n  {B}Type a partial sentence{R} {D}(Enter for 'the capital of france is'){R}: ").strip()
    prompt = (raw or "the capital of france is").lower().rstrip(" .")

    match = difflib.get_close_matches(prompt, list(PROMPTS), n=1, cutoff=0.6)
    if match:
        words, logits = PROMPTS[match[0]]
        print(f"  {D}→ matched known prompt {Y}\"{match[0]}\"{R}")
    else:
        words, logits = GENERIC
        print(f"  {D}→ {Y}not in the precomputed set{R} — using a generic distribution.{R}")

    t_raw = input(f"  {B}Temperature{R} {D}(Enter for 0.7){R}: ").strip()
    try:
        temp = float(t_raw) if t_raw else 0.7
    except ValueError:
        print(f"  {D}(couldn't parse '{t_raw}', using 0.7){R}")
        temp = 0.7

    label = "greedy" if temp <= 0 else ("balanced" if temp < 1 else "creative")
    print(f'\n  Prompt: "{B}{raw or "the capital of france is"}{R} ___"\n')
    print(f"{Y}── temperature = {temp}  ({label}) ──{R}")
    probs = softmax(logits, temp)
    bar_chart(words, probs)
    print(f"\n  {B}Sampling 5 times:{R}")
    rng = random.Random(42)
    picks = [weighted_choice(rng, words, probs) for _ in range(5)]
    print(f"  {G}{', '.join(picks)}{R}")

    print("=" * 60)
    print(f"  {D}temp=0 → always the top token;  temp↑ → flatter, more variety.{R}")
    print("=" * 60)


if __name__ == "__main__":
    main()
