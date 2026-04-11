#!/usr/bin/env python3
"""Demo: see how Scalar and Binary Quantization transform vectors."""
import numpy as np

# --- A tiny vector (pretend it's from an embedding model) ---
vec = np.array([0.234, -0.891, 0.456, -0.123, 0.789, -0.567], dtype=np.float32)

print("=" * 55)
print("  QUANTIZATION: Compress Vectors, Keep Meaning")
print("=" * 55)

# --- Original: FP32 (4 bytes per number) ---
print(f"\n📐 Original (FP32) — 4 bytes per dim:")
print(f"   {vec}")
print(f"   Size: {vec.nbytes} bytes ({len(vec)} dims × 4 bytes)")

# --- Scalar Quantization: FP32 → INT8 ---
# Map the range [min, max] → [0, 255]
def scalar_quantize(v):
    lo, hi = v.min(), v.max()
    return np.round((v - lo) / (hi - lo) * 255).astype(np.uint8)

sq = scalar_quantize(vec)
print(f"\n🔢 Scalar Quantized (INT8) — 1 byte per dim:")
print(f"   {vec}  →  {sq}")
print(f"   Size: {sq.nbytes} bytes  (4x smaller!)")

# --- Binary Quantization: positive → 1, negative → 0 ---
def binary_quantize(v):
    return (v > 0).astype(np.uint8)

bq = binary_quantize(vec)
print(f"\n⚡ Binary Quantized — 1 bit per dim:")
print(f"   {vec}  →  {bq}")
print(f"   Size: {len(bq) // 8 or 1} byte(s)  (32x smaller!)")

# --- Show how BQ comparison works (XOR + popcount) ---
vec2 = np.array([0.198, -0.750, -0.321, -0.089, 0.654, 0.112], dtype=np.float32)
bq2 = binary_quantize(vec2)

xor = np.bitwise_xor(bq, bq2)
hamming = xor.sum()

print(f"\n{'─' * 55}")
print(f"  BQ Distance (Hamming = XOR + count):\n")
print(f"   Vec A bits: {bq}")
print(f"   Vec B bits: {bq2}")
print(f"   XOR:        {xor}")
print(f"   Hamming distance: {hamming}  (lower = more similar)")
print(f"\n  💡 Just bit flips. No multiplication. Lightning fast.")
print(f"{'=' * 55}")
