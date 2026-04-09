#!/usr/bin/env python3
"""Quantization demo — shows BQ/SQ recall vs compression on realistic vectors."""

import numpy as np
import time

# --- Config ---
N_VECTORS = 10_000
N_QUERIES = 50
DIMS = 1536
TOP_K = 10
N_CLUSTERS = 50
CLUSTER_SPREAD = 0.3  # std dev of noise around cluster centers
SQ_RERANK_K = 100
BQ_RERANK_K = 200
SEED = 42


def generate_clustered_vectors(n, dims, n_clusters, spread, centers=None):
    """Generate normalized vectors clustered around centers."""
    if centers is None:
        centers = np.random.randn(n_clusters, dims).astype(np.float32) * 3
    labels = np.random.randint(0, n_clusters, n)
    vecs = centers[labels] + np.random.randn(n, dims).astype(np.float32) * spread
    return (vecs / np.linalg.norm(vecs, axis=1, keepdims=True)).astype(np.float32), centers


def exact_topk(vecs, query, k):
    """Brute-force exact nearest neighbors by dot product."""
    similarities = vecs @ query  # dot product = similarity measure
    top_k_indices = np.argsort(-similarities)[:k]
    return top_k_indices


def scalar_quantize(vecs):
    """Quantize FP32 vectors to UINT8 per-dimension."""
    vmin = vecs.min(axis=0)
    vmax = vecs.max(axis=0)
    scale = vmax - vmin
    scale[scale == 0] = 1
    # Map each float from [vmin, vmax] range into [0, 255] integer buckets
    quantized = ((vecs - vmin) / scale * 255).astype(np.uint8)
    return quantized, vmin, scale


def binary_quantize(vecs):
    """Quantize FP32 vectors to packed 1-bit."""
    # Positive → 1, Negative → 0 (this is the core quantization step)
    sign_bits = (vecs > 0).astype(np.uint8)
    # Pack 8 sign bits into 1 byte (1536 dims → 192 bytes per vector)
    packed = np.packbits(sign_bits, axis=1)
    return packed


def hamming_topk(bq_vecs, bq_query, k):
    """Find top-k by Hamming distance (XOR + popcount)."""
    # XOR: produces 1-bit wherever two vectors differ
    differences = np.bitwise_xor(bq_vecs, bq_query)
    # Count differing bits = Hamming distance
    distances = np.unpackbits(differences, axis=1).sum(axis=1)
    top_k_indices = np.argsort(distances)[:k]
    return top_k_indices


def recall_at_k(predicted, ground_truth):
    """Average recall@k across queries."""
    return np.mean([len(set(p) & set(g)) / len(g) for p, g in zip(predicted, ground_truth)])


def run_demo():
    np.random.seed(SEED)

    print("=" * 65)
    print("  QUANTIZATION DEMO: Precision vs Compression")
    print("=" * 65)

    print(f"\nGenerating {N_VECTORS:,} clustered vectors ({DIMS}d)...")
    print(f"  ({N_CLUSTERS} clusters, spread={CLUSTER_SPREAD})")
    vectors, centers = generate_clustered_vectors(N_VECTORS, DIMS, N_CLUSTERS, CLUSTER_SPREAD)
    queries, _ = generate_clustered_vectors(N_QUERIES, DIMS, N_CLUSTERS, CLUSTER_SPREAD, centers=centers)

    # 1. FP32 exact baseline
    print("\n1. FP32 Exact Search (baseline)...")
    t0 = time.time()
    ground_truth = [exact_topk(vectors, q, TOP_K) for q in queries]
    fp32_time = time.time() - t0

    # 2. Scalar INT8 + re-rank
    print("2. Scalar Quantization (FP32 → INT8 + re-rank)...")
    sq_vectors, vmin, scale = scalar_quantize(vectors)
    t0 = time.time()
    sq_results = []
    for q in queries:
        # Quantize query to same INT8 scale
        sq_query = ((q - vmin) / scale * 255).astype(np.float32)
        # Fast approximate search using INT8 vectors
        approx_sims = sq_vectors.astype(np.float32) @ sq_query
        candidates = np.argsort(-approx_sims)[:SQ_RERANK_K]
        # Re-rank: recompute exact distances on original FP32 vectors
        exact_sims = vectors[candidates] @ q
        sq_results.append(candidates[np.argsort(-exact_sims)[:TOP_K]])
    sq_time = time.time() - t0

    # 3. Binary 1-bit (no re-rank)
    print("3. Binary Quantization (FP32 → 1-bit)...")
    bq_vectors = binary_quantize(vectors)
    bq_queries = binary_quantize(queries)
    t0 = time.time()
    bq_results = [hamming_topk(bq_vectors, bq_queries[i], TOP_K) for i in range(N_QUERIES)]
    bq_time = time.time() - t0

    # 4. Binary + FP32 re-rank
    print("4. Binary Quantization + FP32 Re-rank (top 200 → top 10)...")
    t0 = time.time()
    bq_rerank_results = []
    for i in range(N_QUERIES):
        # Fast coarse pass: find top candidates using Hamming distance
        candidates = hamming_topk(bq_vectors, bq_queries[i], BQ_RERANK_K)
        # Re-rank: recompute exact distances on original FP32 vectors
        exact_sims = vectors[candidates] @ queries[i]
        bq_rerank_results.append(candidates[np.argsort(-exact_sims)[:TOP_K]])
    bq_rerank_time = time.time() - t0

    # Results
    fp32_size = vectors.nbytes
    sq_size = sq_vectors.nbytes
    bq_size = bq_vectors.nbytes

    print(f"\n{'=' * 65}")
    print(f"  RESULTS ({N_VECTORS:,} vectors, {DIMS}d, top-{TOP_K})")
    print(f"{'=' * 65}")
    print(f"  {'Method':<28} {'Size':>8} {'Compress':>9} {'Recall@10':>10} {'Time':>8}")
    print(f"  {'─' * 63}")

    for name, size, results, t in [
        ("FP32 (baseline)", fp32_size, ground_truth, fp32_time),
        ("Scalar INT8 + re-rank", sq_size, sq_results, sq_time),
        ("Binary 1-bit", bq_size, bq_results, bq_time),
        ("Binary + re-rank", bq_size, bq_rerank_results, bq_rerank_time),
    ]:
        r = recall_at_k(results, ground_truth)
        comp = fp32_size / size
        print(f"  {name:<28} {size/1024/1024:>6.0f}MB {comp:>7.0f}x {r:>9.1%} {t:>7.2f}s")

    print(f"\n  💡 KEY INSIGHT:")
    print(f"  Binary + re-rank: {recall_at_k(bq_rerank_results, ground_truth):.0%} recall at {fp32_size/bq_size:.0f}x compression")
    print(f"  Scalar INT8+rr:   {recall_at_k(sq_results, ground_truth):.0%} recall at {fp32_size/sq_size:.0f}x compression")
    print(f"")
    print(f"  In production: Use BQ for fast candidate retrieval (coarse pass),")
    print(f"  then fetch full FP32 vectors from disk to re-rank the final set.")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    run_demo()
