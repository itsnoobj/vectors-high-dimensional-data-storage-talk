#!/usr/bin/env python3
"""Demystifying AI — how text becomes tokens (GPT-style, simulated)."""
import time

# ANSI colors
C = "\033[96m"; G = "\033[92m"; Y = "\033[93m"; D = "\033[2m"; B = "\033[1m"; R = "\033[0m"

# Hardcoded token map: word -> list of subword pieces (simulating BPE).
# Common words = 1 token; rarer/longer words split into pieces.
TOKEN_MAP = {
    "I": ["I"], "love": ["love"], "french": ["french"], "fries": ["fries"],
    "Unbelievable": ["Un", "bel", "iev", "able"], "!": ["!"],
    "The": ["The"], "quick": ["quick"], "brown": ["brown"], "fox": ["fox"],
    "jumps": ["jumps"], "over": ["over"], "the": ["the"], "lazy": ["lazy"],
    "dog": ["dog"], "tokenization": ["token", "ization"],
    "is": ["is"], "fascinating": ["fasc", "inating"], "stuff": ["stuff"],
}


def tokenize(text):
    """Split text into pseudo-tokens using the hardcoded BPE-like map."""
    pieces = []
    for word in text.replace("!", " !").split():
        pieces.extend(TOKEN_MAP.get(word, [word]))
    return pieces


def show(text):
    toks = tokenize(text)
    colored = " ".join(f"{G}[{t}]{R}" for t in toks)
    print(f'  "{B}{text}{R}"')
    print(f"  → {colored}")
    print(f"  {D}words: {len(text.split())}   tokens: {len(toks)}{R}\n")
    time.sleep(0.8)


def main():
    print("=" * 60)
    print(f"  {C}{B}TOKENIZATION: How LLMs Read Text{R}")
    print("=" * 60)
    print(f"\n  {D}Models don't see words — they see tokens.{R}\n")
    time.sleep(0.8)

    print(f"{Y}── Simple words: usually 1 token each ──{R}\n")
    show("I love french fries")

    print(f"{Y}── Rare words: split into subword pieces ──{R}\n")
    show("Unbelievable !")

    print(f"{Y}── A longer sentence ──{R}\n")
    show("The quick brown fox jumps over the lazy dog")
    show("tokenization is fascinating stuff")

    print("─" * 60)
    print(f"  {B}Rule of thumb:{R}  100 words ≈ {G}133 tokens{R}")
    print(f"  {D}(~0.75 words per token in English){R}")
    words = 100
    est_tokens = round(words * 1.33)
    bar_w = "█" * 20
    bar_t = "█" * 27
    print()
    print(f"  words   {C}{bar_w}{R} {words}")
    print(f"  tokens  {G}{bar_t}{R} {est_tokens}")
    print("=" * 60)
    print(f"  {D}Why it matters: you pay per token, and context limits{R}")
    print(f"  {D}are counted in tokens — not words.{R}")
    print("=" * 60)


if __name__ == "__main__":
    main()
