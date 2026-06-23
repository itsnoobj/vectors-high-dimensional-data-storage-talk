#!/usr/bin/env python3
"""Demystifying AI — real next-word prediction using Ollama (local LLM)."""
import json
import urllib.request
import time

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


def generate_one_token(prompt, temperature=0.7):
    """Ask ollama to generate a short completion (1-2 words)."""
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 3, "temperature": temperature},
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    # Take just the first word of the response, strip punctuation
    response = data.get("response", "").strip().lstrip(".,;:!?…\n ")
    first_word = response.split()[0] if response.split() else response
    return first_word


def sample_at_temperature(prompt, temperature, count=8):
    """Sample multiple completions to show distribution."""
    results = []
    for _ in range(count):
        token = generate_one_token(prompt, temperature)
        results.append(token)
    return results


def display_samples(prompt, temperature, samples):
    """Display sampled tokens with frequency."""
    from collections import Counter
    freq = Counter(samples)
    total = len(samples)
    desc = "deterministic" if temperature < 0.1 else "balanced" if temperature < 0.9 else "creative"

    print(f"\n{YELLOW}── temperature = {temperature}  ({desc}) ──{RESET}")
    for token, count in freq.most_common():
        pct = count / total * 100
        bar_len = int(pct / 100 * 25)
        bar = "█" * bar_len
        color = GREEN if count == max(freq.values()) else CYAN
        print(f"    {token:<12} {color}{bar}{RESET} {DIM}{pct:.0f}% ({count}/{total}){RESET}")
    print(f"    {DIM}raw: {', '.join(samples)}{RESET}")


def main():
    print(f"\n{'=' * 60}")
    print(f"  {CYAN}{BOLD}NEXT-WORD PREDICTION: Real LLM ({MODEL}){RESET}")
    print(f"{'=' * 60}")
    print(f"  {DIM}Using Ollama local model — actual inference{RESET}\n")

    # Get prompt
    print(f"{'─' * 60}")
    prompt = input(f"  {BOLD}Type a partial sentence (Enter for default):{RESET} ").strip()
    if not prompt:
        prompt = "Once upon a time there was a"

    print(f"\n  Prompt: \"{BOLD}{prompt}{RESET} ___\"\n")
    print(f"  {DIM}Sampling 8 completions at each temperature...{RESET}")

    # Demo at 3 temperatures
    for temp in [0.0, 0.7, 1.5]:
        samples = sample_at_temperature(prompt, temp)
        display_samples(prompt, temp, samples)

    print(f"\n{'=' * 60}")
    print(f"  {BOLD}Key insight:{RESET}")
    print(f"    temp=0   → same answer every time")
    print(f"    temp=0.7 → mostly consistent, some variety")
    print(f"    temp=1.5 → surprising/creative picks")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
