#!/usr/bin/env python3
"""Demystifying AI — real tokenization using tiktoken (GPT-4 tokenizer)."""
import time
import tiktoken

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

encoder = tiktoken.encoding_for_model("gpt-4")


def display_tokens(text):
    """Tokenize text and display each token with color."""
    token_ids = encoder.encode(text)
    token_strings = [encoder.decode([tid]) for tid in token_ids]
    colored_tokens = " ".join(f"{GREEN}[{t}]{RESET}" for t in token_strings)

    word_count = len(text.split())
    token_count = len(token_ids)

    print(f'  "{BOLD}{text}{RESET}"')
    print(f"   → {colored_tokens}")
    print(f"  {DIM}words: {word_count}   tokens: {token_count}{RESET}\n")


def show_section(title, examples):
    """Display a section header and tokenize each example."""
    time.sleep(0.3)
    print(f"{YELLOW}── {title} ──{RESET}\n")
    for example in examples:
        display_tokens(example)


def get_user_input():
    """Prompt user for a sentence to tokenize."""
    print(f"{'─' * 60}")
    user_text = input(f"  {BOLD}Type a sentence (Enter for default):{RESET} ").strip()
    if not user_text:
        user_text = "The quick brown fox jumps over the lazy dog"
    print()
    return user_text


def show_stats(text):
    """Show token-to-word ratio for the given text."""
    token_ids = encoder.encode(text)
    word_count = max(len(text.split()), 1)
    ratio = len(token_ids) / word_count

    print(f"{'─' * 60}")
    print(f"  {BOLD}Token ratio:{RESET} {ratio:.2f} tokens per word")
    print(f"  {DIM}Rule of thumb: ~1.3 tokens per English word{RESET}")
    print(f"  {DIM}(code/URLs have higher ratios){RESET}")
    print(f"{'=' * 60}\n")


def main():
    print(f"\n{'=' * 60}")
    print(f"  {CYAN}{BOLD}TOKENIZATION: Real GPT-4 Tokenizer (tiktoken){RESET}")
    print(f"{'=' * 60}\n")
    print(f"  {DIM}Using cl100k_base encoding (GPT-4 / ChatGPT){RESET}\n")

    show_section("Simple words", ["I love french fries"])
    show_section("Subword splitting", ["Unbelievable!", "tokenization is fascinating"])
    show_section("Code & special chars", ["def hello_world():", "https://www.example.com/path?q=hello"])

    user_text = get_user_input()
    display_tokens(user_text)
    show_stats(user_text)


if __name__ == "__main__":
    main()
