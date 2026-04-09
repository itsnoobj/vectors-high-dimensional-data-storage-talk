# Storing High-Dimensional Data at Scale

> The RAM Wall, Quantization, Filtered Search & When to Use What

## Overview

Storing vectors has evolved from a niche requirement into a core architectural challenge. This talk covers the modern technical landscape of vector storage — what works, what breaks, and what to use when — with live demos and practical guidance.

## Format

- Demo + visuals - mostly terminal deck
- Database-agnostic concepts with PostgreSQL (pgvector) as the running example

## What We'll Cover

1. **Embeddings & Vector Indexing** — How semantic search works and why vector indexes (HNSW, IVFFlat) are fundamentally different from traditional B-tree indexes

2. **The RAM Wall** — The math behind vector storage costs at scale. Why 100M vectors at 1536 dimensions needs ~920 GB of RAM, and why that's an infrastructure cliff, not a linear cost

3. **Quantization Strategies** — Scalar, Binary, and Product Quantization. The "coarse search + re-rank" production pattern that gives 32x compression with 92-96% recall. Live demo included.

4. **DiskANN** — Disk-optimized indexes that keep compressed data in RAM and full vectors on SSD. How to search billions of vectors on a single node.

5. **The Filtered Search Problem** — Why combining WHERE clauses with vector search silently breaks most indexes. Pre-filter vs post-filter failure modes, and the fixes available today (iterative scan, partial indexes, partitioning). Live SQL demo included.

6. **Architecture: Specialized vs Converged** — The trade-offs between adding a dedicated vector DB vs adding vector support to your existing database. The data sync tax. Hybrid search (BM25 + vectors).

7. **Decision Matrix & Takeaways** — What to use when, mapped to real-world scenarios — from internal knowledge bases to multi-tenant SaaS to billion-scale search.


## Assumptions that folks are familar on:

- SQL databases (PostgreSQL or similar)
- Basic understanding of what embeddings are (text/image → vector of numbers)
- Vector indexing - some idea, we will cover the intuition at high level

