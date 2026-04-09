#!/usr/bin/env python3
"""The RAM Wall Calculator — shows memory/cost at different vector scales."""

DIMS = [384, 768, 1536, 3072]
SCALES = [1_000_000, 10_000_000, 100_000_000, 1_000_000_000]
HNSW_OVERHEAD = 1.5  # 50% graph overhead (varies 30-80% depending on M param)
BYTES_PER_FLOAT = 4
GB = 1024**3

# Approximate AWS r6g monthly cost per GB of RAM (varies by instance size)
COST_PER_GB_MONTH = 4.60  # r6g.xlarge: $0.2016/hr, 32GB → ~$4.59/GB/mo

def fmt_size(b):
    if b >= 1024**4: return f"{b/1024**4:.1f} TB"
    if b >= GB: return f"{b/GB:.1f} GB"
    return f"{b/1024**2:.1f} MB"

def fmt_cost(dollars):
    if dollars >= 1000: return f"${dollars/1000:.0f}K/mo"
    return f"${dollars:.0f}/mo"

print("=" * 72)
print("  THE RAM WALL: Vector Memory & Cost Calculator")
print("=" * 72)

for dim in DIMS:
    per_vec = dim * BYTES_PER_FLOAT
    print(f"\n{'─' * 72}")
    print(f"  {dim} dimensions  |  {per_vec:,} bytes/vector  |  Model examples:", end=" ")
    if dim == 384: print("MiniLM, E5-small")
    elif dim == 768: print("E5-base, BGE-base")
    elif dim == 1536: print("OpenAI text-embedding-3-small")
    else: print("OpenAI text-embedding-3-large")
    print(f"{'─' * 72}")
    print(f"  {'Vectors':>12}  {'Raw Size':>10}  {'+ HNSW':>10}  {'Est. RAM Cost':>14}  {'Verdict'}")

    for n in SCALES:
        raw = n * per_vec
        with_hnsw = raw * HNSW_OVERHEAD
        cost = (with_hnsw / GB) * COST_PER_GB_MONTH
        verdict = "✅ Single node" if with_hnsw < 64 * GB else \
                  "⚠️  Large instance" if with_hnsw < 512 * GB else \
                  "🔴 Cluster needed" if with_hnsw < 2048 * GB else "💀 Rethink approach"
        print(f"  {n:>12,}  {fmt_size(raw):>10}  {fmt_size(with_hnsw):>10}  {fmt_cost(cost):>14}  {verdict}")

print(f"\n{'=' * 72}")
print("  KEY INSIGHT: At 100M+ vectors with 1536d, you MUST use quantization")
print("  or disk-based indexes. RAM-only HNSW becomes cost-prohibitive.")
print(f"{'=' * 72}")

# Show quantization savings
print(f"\n  QUANTIZATION IMPACT (1536d, 100M vectors):")
raw = 100_000_000 * 1536 * 4
print(f"  {'Method':<25} {'Size':>10} {'Savings':>10} {'RAM Cost':>12}")
for name, factor in [("FP32 (baseline)", 1), ("Scalar INT8", 4), ("Product (PQ)", 32), ("Binary (1-bit)", 32)]:
    size = raw / factor * HNSW_OVERHEAD
    print(f"  {name:<25} {fmt_size(size):>10} {f'{factor}x':>10} {fmt_cost((size/GB)*COST_PER_GB_MONTH):>12}")
