# Storing High-Dimensional Data at Scale — Detailed Reference

> Companion document for the presentation. Covers everything in depth with code examples,
> math, references, and production guidance. Use this as a handout or self-study resource.

---

## Table of Contents

1. [The RAM Wall](#1-the-ram-wall)
2. [Quantization Strategies](#2-quantization-strategies)
3. [Disk-Optimized Indexes: DiskANN](#3-disk-optimized-indexes-diskann)
4. [The Filtered Search Problem](#4-the-filtered-search-problem)
5. [Architecture: Specialized vs Converged](#5-architecture-specialized-vs-converged)
6. [Hybrid Search: BM25 + Vectors](#6-hybrid-search-bm25--vectors)
7. [Observability & Performance Metrics](#7-observability--performance-metrics)
8. [Production Checklist](#8-production-checklist)
9. [Decision Matrix](#9-decision-matrix)
10. [References](#10-references)

---

## 1. The RAM Wall

### The Core Problem

High-dimensional vectors are bulky. The standard HNSW index (Hierarchical Navigable Small Worlds) performs best when fully resident in RAM. At scale, this becomes the dominant infrastructure cost.

### The Math

```
Per vector = dimensions × bytes_per_float
           = 1536 × 4 = 6,144 bytes ≈ 6 KB

HNSW graph overhead per vector ≈ M × 2 × sizeof(int) = M × 2 × 4 bytes
  M=16 (default): 128 bytes/vector → ~2% overhead on 1536d
  But layer 0 has 2×M connections, plus metadata, alignment, etc.

Real-world measured overhead (including all graph structures):
  M=16:  30-50% overhead  (Vespa, kindatechnical.com)
  M=32:  50-70% overhead
  M=64:  up to 100% overhead (Weaviate benchmark)

Using 50% as realistic default for M=16 in production.
```

**Formula (ScyllaDB docs):**
```
Memory ≈ N × (D × B + M × 16) × 1.2
  N = number of vectors
  D = dimensions
  B = bytes per dimension (4 for FP32, 2 for FP16)
  M = max connections per node
  1.2 = operational headroom
```

| Scale | Dimensions | Raw Size | + HNSW (50%) | Approx. Monthly Cost |
|-------|-----------|----------|-------------|---------------------|
| 1M | 1536 | 6.1 GB | 9.2 GB | ~$50 |
| 10M | 1536 | 61 GB | 92 GB | ~$500 |
| 100M | 1536 | 614 GB | 920 GB | ~$5,000+ |
| 1B | 1536 | 6.1 TB | 9.2 TB | Not viable (RAM-only) |
| 1M | 384 | 1.5 GB | 2.3 GB | ~$12 |
| 100M | 384 | 153 GB | 230 GB | ~$1,200 |

*Cost estimates based on AWS r6g instance family pricing. Actual costs vary by instance size — larger instances have better per-GB economics.*

### The Infrastructure Cliff

The cost isn't linear because of infrastructure tiers:

- **< 64 GB**: Single instance (r6g.2xlarge). Simple operations.
- **64-512 GB**: Large instance (r6g.16xlarge). Still single node, but expensive.
- **512 GB - 2 TB**: Multiple instances or specialized hardware. Need replication, sharding, load balancing. Operational complexity jumps 10-30x.
- **> 2 TB**: Distributed cluster. Full-time infrastructure team required.

### What To Do

1. **Choose embedding dimensions wisely.** 384d (MiniLM, E5-small) vs 1536d (OpenAI) is a 4x storage difference. Benchmark recall on YOUR data — smaller models often perform within 2-3% of larger ones for domain-specific tasks.

2. **Consider Matryoshka embeddings.** Models like `nomic-embed-text-v1.5` and OpenAI's `text-embedding-3-small` support variable dimensions. You can truncate 1536d to 256d and retain ~95% of retrieval quality. This is the cheapest lever available.

3. **Plan for quantization from day one.** Don't design your system assuming FP32 forever.

### Demo Script

```bash
python scripts/ram_wall_calculator.py
```

Outputs a table showing memory and cost across dimensions (384, 768, 1536, 3072) and scales (1M to 1B), plus quantization savings.

---

## 2. Quantization Strategies

### Overview

Quantization reduces the precision of stored vectors to save memory. The key insight: you don't need full precision for the *search* step — only for the final *ranking* step.

### Scalar Quantization (SQ)

**How it works:** Map each FP32 value to an INT8 value (0-255) using min/max scaling per dimension.

```python
# Per-dimension quantization
vmin = vectors.min(axis=0)
vmax = vectors.max(axis=0)
scale = vmax - vmin
quantized = ((vectors - vmin) / scale * 255).astype(np.uint8)
```

**Impact:**
- 4x compression (4 bytes → 1 byte per dimension)
- Recall: typically 97-99% with re-ranking
- Supported by: Qdrant, Weaviate, Milvus, pgvectorscale
- pgvector native: use `halfvec` type for FP16 (2x compression, zero recall loss)

**When to use:** When you need high recall and moderate compression. `halfvec` in pgvector is the easiest win — drop-in replacement with 2x savings.

### Product Quantization (PQ)

**How it works:** Split each vector into `m` subvectors. For each subvector, train a codebook of `k` centroids using k-means. Replace each subvector with its nearest centroid ID.

```
Original: [v1, v2, ..., v1536]
Split:    [v1..v192] [v193..v384] ... [v1345..v1536]  (8 subvectors)
Quantize: [centroid_42] [centroid_7] ... [centroid_198]
Store:    8 bytes (one byte per subvector ID, k=256)
```

**Impact:**
- 8x-64x compression depending on configuration
- Recall: 90-97% with re-ranking (depends heavily on data distribution)
- Requires training phase on representative data
- Supported by: FAISS, Milvus, Qdrant, DiskANN

**When to use:** Massive datasets (100M+) where you need extreme compression and can tolerate a training step.

### Binary Quantization (BQ)

**How it works:** Convert each dimension to a single bit. Positive → 1, negative → 0.

```python
binary = (vectors > 0).astype(np.uint8)
packed = np.packbits(binary, axis=1)  # 1536 dims → 192 bytes
```

**Impact:**
- 32x compression (4 bytes → 1 bit per dimension)
- Distance computation becomes Hamming distance (XOR + popcount)
- Hardware-accelerated: modern CPUs have dedicated `POPCNT` instructions
- Recall alone: 85-95% (model-dependent)
- Recall with re-ranking: 95-99%
- pgvector native: use `bit` type (since 0.7) for binary vector storage and indexing

**When to use:** When you need maximum compression and speed. Best with models designed for BQ (Cohere embed-v3, Jina v3). Older models may have lower BQ recall.

**Newer variant — Rotational Quantization (RQ):** Weaviate (since v1.32, default since v1.33) applies a pseudorandom rotation before quantizing, spreading information evenly across dimensions. Achieves 98-99% recall at 4x compression without training. This is the current state of the art for quantization that "just works."

### The Production Pattern: Coarse + Re-rank

```
1. Query arrives
2. Binary search: XOR + popcount against BQ index (in RAM)
   → Returns top 1000 candidates (microseconds)
3. Fetch FP32 vectors for those 1000 candidates (from SSD/disk)
4. Exact cosine similarity re-ranking
   → Returns top 10 results
```

This two-phase approach gives you:
- **Speed** of binary search (32x less memory, hardware-accelerated)
- **Accuracy** of full-precision ranking (only on a small candidate set)

### Model-Dependence of BQ

Not all embedding models work equally well with binary quantization. The key factor is how much information is preserved in the sign of each dimension.

| Model | BQ Recall@10 (no re-rank) | BQ + Re-rank (top 200) |
|-------|--------------------------|----------------------|
| Cohere embed-v3 | ~92% | ~99% |
| Jina v3 | ~90% | ~98% |
| OpenAI text-embedding-3-small | ~85% | ~96% |
| all-MiniLM-L6-v2 | ~80% | ~93% |

*Approximate figures. Actual recall depends on dataset and query distribution.*

Models trained with BQ awareness (Cohere, Jina) distribute information more evenly across dimensions, making the sign bit more informative.

### Demo Script

```bash
python scripts/quantization_demo.py
```

Generates 10K clustered vectors (1536d), applies SQ and BQ, measures recall@10 against exact search. Shows the BQ + re-rank pattern achieving ~99% recall at 32x compression.

---

## 3. Disk-Optimized Indexes: DiskANN

### Why DiskANN?

HNSW was designed when datasets fit in RAM. DiskANN (Disk-optimized Approximate Nearest Neighbors) was designed for the SSD era.

**Paper:** Jayaram Subramanya et al., "DiskANN: Fast Accurate Billion-point Nearest Neighbor Search on a Single Node" (NeurIPS 2019). Developed at Microsoft Research, used in Bing.

### How It Works

```
RAM:  [Compressed graph structure + PQ codes for each vector]
      Used for graph traversal and approximate distance computation

SSD:  [Full-precision FP32 vectors]
      Fetched only for final candidates during re-ranking
```

Key design decisions:
1. **Graph layout optimized for sequential SSD reads.** Neighbors in the graph are stored contiguously on disk to minimize random I/O.
2. **PQ codes in RAM for traversal.** During graph navigation, distances are computed using compressed PQ codes (tiny), not full vectors.
3. **Beam search with SSD prefetching.** Multiple graph paths are explored simultaneously, with SSD reads pipelined.

### Comparison

| Factor | HNSW | Quantized HNSW | DiskANN |
|--------|------|---------------|---------|
| Dataset sweet spot | < 50M | 50-200M | 100M – 1B+ |
| RAM (100M, 1536d) | ~920 GB | ~30-60 GB | ~10-20 GB |
| Latency (p50) | 1-5ms | 2-8ms | 5-15ms |
| Latency (p99) | 5-20ms | 10-30ms | 15-50ms |
| Build time (100M) | 1-3 days | 1-3 days | 4-8 hours |
| Incremental inserts | Yes | Yes | Limited |
| Maturity | Battle-tested | Mature | Rapidly maturing |

**Important:** The comparison should be HNSW vs Quantized HNSW vs DiskANN — not just vanilla HNSW vs DiskANN. Quantized HNSW is often the right middle ground.

### Availability

- **Azure Database for PostgreSQL:** `pg_diskann` extension — DiskANN went GA in May 2025. Claims "10x faster, 4x lower cost, 96x lower memory footprint vs pgvector HNSW." Supports up to 16,000 dimensions and iterative post-filtering.
- **pgvectorscale (Timescale):** Open-source PostgreSQL extension using StreamingDiskANN. Claims 28x lower p95 latency and 16x higher throughput vs Pinecone's storage-optimized index. Not available on RDS/Aurora — requires self-managed PostgreSQL or Timescale Cloud.
- **Microsoft DiskANN:** Open source (github.com/microsoft/DiskANN)
- **Milvus:** Supports DiskANN index type
- **LanceDB:** Built on DiskANN principles
- **Turbopuffer:** Serverless vector DB using disk-based indexes

### When to Use DiskANN

- Dataset > 50M vectors AND you can't afford the RAM for HNSW
- Latency budget allows 5-15ms (not sub-5ms)
- You have fast NVMe SSDs (DiskANN performance is directly tied to SSD IOPS)
- You don't need frequent incremental updates (DiskANN rebuild is faster than HNSW but still significant)

---

## 4. The Filtered Search Problem

### The Problem

In production, you rarely search the entire vector space. You search within a subset:

```sql
SELECT * FROM products
WHERE tenant_id = 42 AND category = 'electronics'
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

### Why Both Naive Approaches Fail

**Pre-filtering (filter first, then ANN):**
```
50,000 docs → WHERE tenant_id = 42 → 200 docs → ANN search
```
Problem: The 200 matching docs are scattered across the HNSW graph. The graph structure is useless — you end up doing a sequential scan on 200 vectors. At small filter sizes, this is fine. At medium sizes (1K-10K matching docs), it's the worst of both worlds.

**Post-filtering (ANN first, then filter):**
```
50,000 docs → ANN top 100 → WHERE tenant_id = 42 → 3 results (or 0!)
```
Problem: If only 0.4% of docs match tenant_id=42, then statistically only 0.4 of your top 100 ANN results will match. You get 0-1 results instead of 10.

### Solutions by Filter Cardinality

| Filter Cardinality | Strategy | How It Works |
|-------------------|----------|-------------|
| Any (pgvector 0.8+) | `iterative_scan` | Scans index → applies filter → if not enough results, scans more. The default solution now. |
| Very low (2-10 values) | Partial indexes | One HNSW index per filter value. `CREATE INDEX ... WHERE category = 'science'` |
| Low (10-100 values) | Partial indexes | Same, but more indexes. Monitor index count and build time. |
| Medium (100-10K values) | Table partitioning | `PARTITION BY LIST (tenant_id)`. Each partition gets its own HNSW index. |
| High (10K+ values) | `iterative_scan` + high ef | Set `hnsw.ef_search` high (200-500), let iterative scan handle the rest. |
| Any | Integrated filtered traversal | Database checks metadata bitmap during graph walk. Available in Qdrant, Weaviate, Azure PostgreSQL DiskANN. |

### pgvector 0.8+: iterative_scan (The Game Changer)

Before pgvector 0.8, filtered search was the biggest pain point. With `hnsw.ef_search = 40` and a filter matching 10% of rows, you'd get ~4 results instead of 10 on average.

The `iterative_scan` feature (released Nov 2024) fixes this:

```sql
-- Enable iterative scanning
SET hnsw.iterative_scan = relaxed_order;

-- Now this reliably returns 10 results even with selective filters
SELECT id, content,
  embedding <=> (SELECT embedding FROM docs WHERE id = 97) AS dist
FROM docs
WHERE metadata->>'tenant_id' = '42'
ORDER BY embedding <=> (SELECT embedding FROM docs WHERE id = 97)
LIMIT 10;
```

How it works: scan the index → apply filter → check if enough results → if not, scan more of the index. Simple but effective.

### PostgreSQL Example: Partial Indexes (Still Useful)

```sql
-- Create partial HNSW index for each category
CREATE INDEX docs_hnsw_science ON docs
  USING hnsw (embedding vector_cosine_ops)
  WHERE metadata->>'category' = 'science';

CREATE INDEX docs_hnsw_tech ON docs
  USING hnsw (embedding vector_cosine_ops)
  WHERE metadata->>'category' = 'tech';

-- Query uses the partial index automatically
SELECT id, content,
  embedding <=> (SELECT embedding FROM docs WHERE id = 97) AS dist
FROM docs
WHERE metadata->>'category' = 'science'
ORDER BY embedding <=> (SELECT embedding FROM docs WHERE id = 97)
LIMIT 10;
```

### PostgreSQL Example: Table Partitioning for Multi-Tenancy

```sql
-- Partition by tenant
CREATE TABLE docs_partitioned (
    id serial,
    tenant_id int,
    content text,
    embedding vector(1536)
) PARTITION BY LIST (tenant_id);

-- Create partitions
CREATE TABLE docs_tenant_1 PARTITION OF docs_partitioned FOR VALUES IN (1);
CREATE TABLE docs_tenant_2 PARTITION OF docs_partitioned FOR VALUES IN (2);
-- ... etc

-- Each partition gets its own HNSW index
CREATE INDEX ON docs_tenant_1 USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON docs_tenant_2 USING hnsw (embedding vector_cosine_ops);

-- Query automatically routes to correct partition
SELECT * FROM docs_partitioned
WHERE tenant_id = 1
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

### The Overfetch Pattern (High Cardinality)

When you can't create per-value indexes:

```sql
-- Increase ef_search to overfetch candidates
SET hnsw.ef_search = 500;  -- default is 40

-- The index returns ~500 candidates internally,
-- then the WHERE clause filters them
SELECT * FROM docs
WHERE metadata->>'user_id' = '12345'
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

Trade-off: Higher ef_search = more candidates = better chance of finding matches after filtering, but slower queries. You're trading latency for recall.

---

## 5. Architecture: Specialized vs Converged

### The Trade-offs (Honest Assessment)

| Factor | Specialized Vector DB | Converged DB |
|--------|----------------------|--------------|
| **Examples** | Pinecone, Qdrant, Weaviate, Milvus | pgvector, Oracle 23ai, Mongo Atlas |
| **Ops complexity** | New stack (but managed options exist) | Reuse existing infra |
| **Data consistency** | Eventual (must sync with primary DB) | ACID compliant |
| **Metadata joins** | Limited or proprietary query language | Full SQL / native query language |
| **Vector features** | Ahead (BQ, DiskANN, hybrid, multi-modal) | Catching up, 6-12 months behind |
| **Scaling ceiling** | Higher (purpose-built for vectors) | Lower (general-purpose DB) |
| **Vendor lock-in** | High (proprietary APIs) | Low |
| **Managed options** | Pinecone Serverless, Qdrant Cloud | RDS, Aurora, Cloud SQL |

### The Data Sync Tax (Specialized DB)

When your source of truth is PostgreSQL but your search index is Pinecone:

```
Write path:
  App → PostgreSQL (INSERT/UPDATE/DELETE)
      → Sync pipeline (Kafka/CDC/webhook)
      → Vector DB (upsert embedding)

Failure modes:
  1. Vector DB write fails → stale search results
  2. Document deleted from Postgres → ghost results in vector DB
  3. Embedding model updated → must re-embed everything in both systems
  4. User permissions change → vector DB returns unauthorized results
  5. Schema migration → must update both systems atomically
```

**Mitigation:** Managed services (Pinecone Serverless, Qdrant Cloud) reduce operational burden. CDC tools (Debezium) automate sync. But the fundamental consistency problem remains.

### The pgvector Pain Points (Converged DB)

Being honest about pgvector's limitations at scale:

1. **Index build time:** HNSW on 10M vectors can take 4-8 hours. During this time, `CREATE INDEX CONCURRENTLY` holds a lock that blocks other index operations.

2. **VACUUM pressure:** MVCC means every UPDATE copies the entire row including the embedding. Frequent metadata updates on embedding tables cause massive TOAST bloat. Mitigation: separate embedding tables.

3. **No built-in hybrid search:** pgvector does vector search. For BM25 keyword search, you need `pg_trgm` (basic) or ParadeDB's `pg_search` (full BM25). Application-level fusion is common.

4. **Query planner limitations:** PostgreSQL's cost model doesn't understand vector operations well. Sometimes it chooses sequential scan over index scan incorrectly. Workaround: `SET enable_seqscan = off` for vector queries.

5. **pgvectorscale not on RDS/Aurora:** Timescale's DiskANN extension requires self-managed PostgreSQL or Timescale Cloud.

### The Industry Trend

The trend is toward converged, but it's not universal:

- **Estuary.dev (Dec 2025):** "The Vector Database Hype is Over" — argues co-locating vectors with your primary database reduces cost and complexity for most teams.
- **Timescale (2025):** pgvectorscale's StreamingDiskANN claims 28x lower p95 latency and 16x higher throughput vs Pinecone's storage-optimized index.
- **Azure (May 2025):** DiskANN on Azure Database for PostgreSQL went GA — "10x faster, 4x lower cost, 96x lower memory vs pgvector HNSW."
- **pgvector 0.8 (Nov 2024):** `iterative_scan`, `halfvec`, `bit` type — closed the biggest feature gaps vs specialized DBs.
- **Counterpoint — Qdrant (2025):** "Start with pgvector: Why You'll Outgrow It Faster Than You Think" — documents real production pain points at scale.
- **Counterpoint — Alex Jacobs (2025):** "The Case Against pgvector" — details index build time, VACUUM pressure, and query planner issues at scale. Widely shared by Simon Willison.

### Decision Framework

**Choose converged (pgvector, Mongo Atlas, etc.) when:**
- < 50M vectors
- Strong metadata filtering / JOIN requirements
- Team already operates the database
- ACID consistency matters
- Budget-constrained (no new infrastructure)

**Choose specialized (Qdrant, Pinecone, Milvus) when:**
- \> 100M vectors with sub-10ms p99 latency
- Multi-modal search (text + image + audio)
- Need cutting-edge features (filtered HNSW, BQ, streaming indexing)
- Dedicated ML platform team
- Can tolerate eventual consistency

---

## 6. Hybrid Search: BM25 + Vectors

### Why Hybrid?

Vector search finds semantically similar content. Keyword search finds exact matches. Neither alone is sufficient for production retrieval.

```
Query: "PostgreSQL VACUUM deadlock error"

Vector search: Finds "autovacuum lock contention troubleshooting"
  → Semantically related, but misses the exact error message

BM25 search: Finds "ERROR: deadlock detected during VACUUM"
  → Exact match, but misses related concepts

Hybrid: Returns both, ranked by combined relevance
  → Best recall
```

### Reciprocal Rank Fusion (RRF)

The standard method for combining results from multiple retrieval systems:

```python
def rrf_score(rank, k=60):
    return 1.0 / (k + rank)

# Combine rankings from vector search and BM25
for doc in all_candidates:
    score = 0
    if doc in vector_results:
        score += rrf_score(vector_results[doc].rank)
    if doc in bm25_results:
        score += rrf_score(bm25_results[doc].rank)
    doc.combined_score = score

# Sort by combined score
results = sorted(all_candidates, key=lambda d: d.combined_score, reverse=True)
```

### PostgreSQL Options

**Option 1: pgvector + pg_trgm (built-in, basic)**
```sql
-- Trigram similarity for fuzzy keyword matching
SELECT content,
  (1 - (embedding <=> query_embedding)) * 0.7 +
  similarity(content, 'VACUUM deadlock') * 0.3 AS combined_score
FROM docs
WHERE content % 'VACUUM deadlock'  -- trigram filter
ORDER BY combined_score DESC
LIMIT 10;
```

**Option 2: pgvector + ParadeDB pg_search (full BM25)**
```sql
-- ParadeDB provides real BM25 scoring via Tantivy
SELECT content,
  paradedb.score(id) AS bm25_score,
  1 - (embedding <=> query_embedding) AS vector_score
FROM docs
WHERE content @@@ 'VACUUM deadlock'  -- BM25 search
ORDER BY paradedb.score(id) * 0.3 + (1 - (embedding <=> query_embedding)) * 0.7 DESC
LIMIT 10;
```

**Option 3: Application-level RRF**
```python
# Query both systems independently, merge results
vector_results = db.execute("SELECT id, embedding <=> %s AS dist FROM docs ORDER BY dist LIMIT 100", [query_emb])
bm25_results = db.execute("SELECT id, ts_rank(tsv, query) AS rank FROM docs WHERE tsv @@ query ORDER BY rank DESC LIMIT 100")

# Apply RRF
combined = reciprocal_rank_fusion(vector_results, bm25_results, k=60)
return combined[:10]
```

---

## 7. Observability & Performance Metrics

### Recall vs Latency

You cannot have both perfect recall AND low latency with approximate indexes. Every system operates on a Pareto frontier.

**How to measure recall:**
```sql
-- 1. Get ground truth (exact search, slow)
SET enable_indexscan = off;
SELECT id FROM docs
ORDER BY embedding <=> (SELECT embedding FROM docs WHERE id = 97)
LIMIT 10;
-- Save these IDs as ground_truth

-- 2. Get ANN results (fast)
SET enable_seqscan = off;
SET hnsw.ef_search = 40;
SELECT id FROM docs
ORDER BY embedding <=> (SELECT embedding FROM docs WHERE id = 97)
LIMIT 10;
-- Save these IDs as ann_results

-- 3. Recall = |intersection| / |ground_truth|
-- If 9 of 10 IDs match → 90% recall
```

**Tuning knobs:**

| Parameter | Effect | Trade-off |
|-----------|--------|-----------|
| `hnsw.ef_search` | Higher = more candidates explored | Recall ↑, Latency ↑ |
| `ivfflat.probes` | Higher = more clusters searched | Recall ↑, Latency ↑ |
| HNSW `m` (build) | Higher = more graph connections | Recall ↑, Index size ↑, Build time ↑ |
| HNSW `ef_construction` (build) | Higher = better graph quality | Recall ↑, Build time ↑ |

### Index Build Time

| Dataset | IVFFlat | HNSW | DiskANN |
|---------|---------|------|---------|
| 50K | ~30s | ~2-5 min | ~1 min |
| 1M | ~5 min | ~30-60 min | ~10 min |
| 10M | ~30 min | ~4-8 hours | ~1 hour |
| 100M | ~3 hours | ~1-3 days | ~4-8 hours |

**Critical operational questions:**
- Can you build indexes without blocking writes? (`CREATE INDEX CONCURRENTLY` in PostgreSQL)
- What's your re-indexing strategy when embedding models change?
- HNSW supports incremental inserts. IVFFlat may need periodic rebuild as data distribution shifts.

### Cost Per Query

```
Cost per query ≈ (CPU time × instance cost/hour) / queries/hour

Example (r6g.xlarge, ~$0.20/hr):
  HNSW query: ~5ms CPU → $0.00000028 per query
  Seq scan:   ~500ms CPU → $0.000028 per query

  At 1M queries/day:
    HNSW:     ~$0.28/day
    Seq scan: ~$28/day
```

**Hidden costs:**
- TOAST I/O for embeddings > 2KB (1024d+)
- VACUUM overhead from MVCC bloat on updates
- Index memory pressure causing OS page cache eviction
- Connection pooling overhead for concurrent vector queries

---

## 8. Production Checklist

### Storage

- [ ] **Separate embedding tables.** Don't let metadata UPDATEs duplicate 4KB+ vectors via MVCC.
- [ ] **Choose dimensions wisely.** 384d stays inline in PostgreSQL heap (< 2KB). 1024d+ gets TOASTed (extra I/O on every read).
- [ ] **Evaluate Matryoshka embeddings.** Can you use 256d instead of 1536d with < 3% recall loss?

### Indexing

- [ ] **Build indexes AFTER bulk load.** Not during. `INSERT` → `CREATE INDEX` → `ANALYZE`.
- [ ] **Always use LIMIT with ORDER BY distance.** Without LIMIT, PostgreSQL ignores ANN indexes.
- [ ] **Tune for YOUR recall/latency target.** Don't use defaults blindly. Measure recall against exact search.
- [ ] **Plan re-indexing strategy.** Embedding models change. You will re-embed. How long does a full rebuild take?

### Operations

- [ ] **Monitor TOAST size.** `SELECT pg_size_pretty(pg_relation_size(reltoastrelid)) FROM pg_class WHERE relname = 'your_table';`
- [ ] **Monitor VACUUM stats.** Dead tuples in embedding tables = bloat.
- [ ] **Set `maintenance_work_mem` high for index builds.** At least 512MB, ideally 1-2GB.
- [ ] **Test filtered search patterns.** Pre-filter, post-filter, partial indexes — know which works for your access patterns.

### Architecture

- [ ] **Start with your existing database.** Add pgvector / native vector support.
- [ ] **Plan for hybrid search.** BM25 + vector retrieval with RRF.
- [ ] **Define your scale trajectory.** At what point do you need quantization? DiskANN? A specialized DB?
- [ ] **Document your consistency requirements.** Can you tolerate eventual consistency for search results?

---

## 9. Decision Matrix

| Scenario | Recommendation | Why |
|----------|---------------|-----|
| < 1M vectors, single app | pgvector + HNSW | Simple, fast, ACID. Done. |
| 1-10M, metadata filters | pgvector + partial indexes + partitioning | Handles most production workloads. |
| 10-50M, cost-sensitive | Quantized HNSW (BQ + re-rank) | 32x compression, ~99% recall. |
| 50M-1B | DiskANN (pgvectorscale, Milvus, LanceDB) | RAM-only is too expensive. |
| Multi-tenant SaaS | Partition by tenant + per-partition indexes | Isolation + performance. |
| Need hybrid search | ParadeDB, Elasticsearch, or app-level RRF | BM25 + vector is the production standard. |
| Sub-5ms p99 at 100M+ | Specialized vector DB (Qdrant, Pinecone) | Purpose-built for this. |
| Multi-modal (text+image) | Specialized vector DB | Converged DBs don't support this well yet. |
| Already on Mongo/Elastic | Use their native vector support | Don't add another database. |

---

## 10. References

### Papers
- Jayaram Subramanya et al., "DiskANN: Fast Accurate Billion-point Nearest Neighbor Search on a Single Node" (NeurIPS 2019)
- Malkov & Yashunin, "Efficient and Robust Approximate Nearest Neighbor using Hierarchical Navigable Small World Graphs" (2018)
- Jégou et al., "Product Quantization for Nearest Neighbor Search" (IEEE TPAMI, 2011)

### HNSW Memory Overhead Sources
- Vespa, "Billion-scale vector search using hybrid HNSW-IF" (2022) — reports 20-40% overhead — medium.com/vespa
- Weaviate, "HNSW+PQ: Exploring ANN algorithms" (2023) — shows up to 100% at M=64 — weaviate.io/blog/ann-algorithms-hnsw-pq
- Lantern, "Estimating memory footprint of your HNSW index" — interactive calculator — lantern.dev/blog/calculator
- ScyllaDB, "Vector Search Sizing" — formula: N × (D × B + M × 16) × 1.2 — cloud.docs.scylladb.com
- kindatechnical.com, "Scaling Retrieval: Billions of Vectors" — reports 30-50% — kindatechnical.com/mlops-guide

### Industry Reports & Surveys
- "The Vector Database Hype is Over" — Estuary.dev (Dec 2025) — estuary.dev/blog/the-vector-database-hype-is-over
- "The Case Against pgvector" — Alex Jacobs (2025) — alex-jacobs.com/posts/the-case-against-pgvector
- "Start with pgvector: Why You'll Outgrow It" — Qdrant (2025) — qdrant.tech/blog/pgvector-tradeoffs
- DiskANN on Azure PostgreSQL GA — Microsoft (May 2025) — techcommunity.microsoft.com
- Timescale pgvectorscale benchmarks — timescale.com/blog/pgvector-is-now-as-fast-as-pinecone

### Technical References
- pgvector 0.8 (iterative_scan, halfvec, bit): github.com/pgvector/pgvector
- pgvectorscale (StreamingDiskANN): github.com/timescale/pgvectorscale
- DiskANN: github.com/microsoft/DiskANN
- Weaviate Rotational Quantization: weaviate.io/blog/8-bit-rotational-quantization
- Elastic BBQ: elastic.co/search-labs/blog/bbq-implementation-into-use-case
- ParadeDB (BM25 + vector hybrid): paradedb.com
- Qdrant Filtered HNSW: qdrant.tech/articles/filtrable-hnsw
- Hugging Face Embedding Quantization (2024): huggingface.co/blog/embedding-quantization

### Tools
- FAISS (Facebook AI Similarity Search): github.com/facebookresearch/faiss
- LanceDB: lancedb.com
- Turbopuffer: turbopuffer.com
