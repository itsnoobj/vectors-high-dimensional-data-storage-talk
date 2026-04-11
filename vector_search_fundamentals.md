---
title: "Vector Search Fundamentals"
sub_title: "From Text Comparison to Production Search — The Magic Unboxed"
author: "Narrated by: Jeevan"
date: "April 2026"
---

# Why This Talk, Why Now

<!-- column_layout: [2, 1] -->

<!-- column: 0 -->

Every team is adding vector search. Few are planning for what happens next.

<!-- pause -->

**The pattern we keep seeing:**

```
Month 1:  "Let's add semantic search!"
          → 100K vectors, works great ✅

Month 4:  "Scale to all our docs"
          → 10M vectors, still fine ✅

Month 8:  "Enterprise rollout"
          → 100M vectors, RAM bill explodes 💸

Month 9:  "Add per-tenant filtering"
          → recall silently drops to 40% 🔇

Month 10: "Maybe we need a vector DB?"
          → now syncing two databases forever 🔄
```

<!-- column: 1 -->

![](images/gifs/flipping-papers.gif)

<!-- reset_layout -->

<!-- pause -->

**This talk gives the mental model to make these decisions *before* month 8.**

<!-- end_slide -->

# Our Journey Today (25 min)

**By the end — how vector search works under the hood,
and what breaks at production scale.**

<!-- column_layout: [1, 1] -->

<!-- column: 0 -->

## 1. The Comparison Problem (~5 min)
- How do computers compare text?
- The magic: text → numbers
- Distance = similarity

## 2. Searching at Scale (~5 min)
- The brute force problem
- Why traditional indexes can't help
- Approximate Nearest Neighbors

## 3. Two Index Strategies (~7 min)
- IVFFlat: cluster & search
- HNSW: multi-layer graph
- When to use which

<!-- column: 1 -->

## 4. The Scale Wall (~4 min)
- The RAM math that breaks budgets
- Quantization: compress smartly
- Disk-based indexes

## 5. Production Reality (~4 min)
- Filtered search: the hidden trap
- Hybrid search: keywords + vectors
- Decision matrix & takeaways

<!-- end_slide -->

# Chapter 1: How Do Computers Compare Text?

**The fundamental problem: computers don't understand words.**

```
"I love pizza"   vs   "Pizza is great"
```

<!-- pause -->

A human instantly knows these are similar.
A computer sees two completely different strings of characters.

<!-- pause -->

**So how do we teach a machine that these mean the same thing?**

![](images/gifs/mind-blown.gif)

<!-- end_slide -->

# Numbers Are Easy to Compare

**Computers are great at comparing numbers:**

```
Temperature today:  32°C
Temperature yesterday: 30°C
→ Difference = 2°C  ✓  Easy!
```

<!-- pause -->

**But text?**

```
"I love pizza"
"Pizza is great"
→ Difference = ???  🤷
```

<!-- pause -->

**The breakthrough idea:** What if we could turn text into numbers?

Not random numbers — numbers that *capture meaning*.

<!-- end_slide -->

# <span style="color: #f9e2af">Embeddings:</span> Text → Numbers That Capture Meaning

**An embedding model converts text into a list of numbers (a "vector"):**

```
"I love pizza"     → [0.2, 0.8, 0.1, ... 384 numbers]
"Pizza is great"   → [0.3, 0.7, 0.2, ... 384 numbers]
"The sky is blue"  → [0.9, 0.1, 0.8, ... 384 numbers]
```

<!-- pause -->

**The magic:** <span style="color: #a6e3a1">Similar meanings → similar numbers!</span>

<!-- pause -->

**Analogy:** 📍 GPS coordinates for meaning

Just like GPS turns "India Gate" into `(28.61, 77.22)` and
"Rashtrapati Bhavan" into `(28.61, 77.19)` — close on a map because they're close in Delhi —

an embedding model places "pizza" and "great food" close together
in a 384-dimensional "meaning space."

<!-- end_slide -->

# 💻 Demo: See It In Action

**Let's prove that similar meaning → similar numbers:**

```bash
python scripts/embedding_intro.py
```

<!-- pause -->

**Compare any two sentences:**

```bash
python scripts/compare.py
```

<!-- end_slide -->

# How Do We Measure "Close"?

<!-- column_layout: [3, 2] -->

<!-- column: 0 -->

**Distance between two points — already familiar:**

```
Point A = (x₁, y₁)    Point B = (x₂, y₂)

Distance = √((x₂-x₁)² + (y₂-y₁)²)
```

**Same idea, just more dimensions:**

```
Vector A = [0.2, 0.8, 0.1, ... 384 nums]
Vector B = [0.3, 0.7, 0.2, ... 384 nums]

Distance = √((0.3-0.2)² + (0.7-0.8)² + ...)
```

**That's Euclidean distance.
But there are better options for text...**

<!-- column: 1 -->

![](images/dist-2-points.png)

<!-- end_slide -->

# Three Ways to Measure Distance

![](images/gifs/compare-vectors.gif)

<!-- column_layout: [1, 4, 1] -->

<!-- column: 0 -->

<!-- column: 1 -->

| Method | Formula | Meaning | Best For |
|--------|---------|---------|----------|
| **Euclidean (L2)** | √(Σ(aᵢ - bᵢ)²) | How far apart? | Images, spatial |
| **Cosine** | 1 - (a·b)/(‖a‖‖b‖) | Same direction? | Text (most common) |
| **Inner Product** | -(a·b) | How aligned? | Normalized vectors |

<!-- column: 2 -->

<!-- reset_layout -->

<!-- pause -->

**For text search, <span style="color: #a6e3a1">cosine is king.</span>** It cares about
*direction* (meaning), not *magnitude* (length).

<!-- end_slide -->

# Putting It All Together

**The complete flow:**

```
1. User asks: "best Italian restaurants"
                    ↓
2. Embedding model: [0.72, 0.82, 0.08, ...]
                    ↓
3. Compare against every stored vector using cosine distance
                    ↓
4. Return closest matches:
   "Amazing pizza place downtown"     → distance: 0.08  ✓
   "Great pasta and wine bar"         → distance: 0.12  ✓
   "How to fix a flat tire"           → distance: 0.95  ✗
```

<!-- pause -->

**Key insight:** <span style="color: #a6e3a1">Lower distance = more similar. Always.</span>

**This is semantic search.** <span style="color: #f9e2af">No keyword matching. Pure meaning.</span>

<!-- end_slide -->

# 💻 Demo: Semantic Search End-to-End

```bash
python scripts/semantic_search_demo.py
```

<!-- pause -->

- 10 PostgreSQL docs → embedded into 384d vectors
- Query: *"how to find and fix slow database queries"*
- Returns matches by **meaning**, not keywords

<!-- end_slide -->

# Chapter 2: The Scale Problem

**So we've solved search, right? Just compare vectors and return the closest ones?**

**...Not quite.** There's a catch.

<!-- pause -->

**To find the closest vectors, we compared against *every* stored vector.**

```
10 documents     → 10 comparisons     → instant
1,000 documents  → 1,000 comparisons  → fast
1,000,000 docs   → 1,000,000 comparisons → 😰
100,000,000 docs → 100,000,000 comparisons → 💀
```

<!-- pause -->

*It's like finding a specific book in a library with no catalog — you'd have to check every shelf.*

![](images/gifs/flipping-papers.gif)

<!-- end_slide -->

# Why Traditional Indexes Can't Help

<!-- column_layout: [1, 1] -->

<!-- column: 0 -->

**In a regular database:**

```sql
SELECT * FROM users
WHERE email = 'alice@example.com';
```

B-tree index → binary search. Fast.

![](images/btree.png)

<!-- pause -->

**But for vectors:**

```sql
SELECT * FROM docs
ORDER BY distance(embedding, query)
LIMIT 10;
```

No natural sort order for "closest to
this 384-dimensional point."
B-trees need linear ordering.
<span style="color: #f38ba8">Vectors don't have one.</span>

<!-- column: 1 -->

```
[0.23, -0.89, 0.45, 0.12, -0.67, ...]
[0.91, 0.03, -0.44, 0.78, 0.15, ...]
[0.17, 0.62, -0.33, -0.51, 0.88, ...]

Sort these? By which number? 🤷
```

![](images/gifs/exact-search-slow.png)

<!-- reset_layout -->

<!-- pause -->

<span style="color: #f9e2af">**If not exact... what if we search *approximately*?**</span>

<!-- pause -->

**We need a different kind of index entirely.**

<!-- end_slide -->

# The Key Insight: <span style="color: #a6e3a1">Approximate Is Good Enough</span>

**What if we don't need the *exact* top 10?**

**What if finding 9 out of 10 true best matches is acceptable?**

<!-- pause -->

This is <span style="color: #a6e3a1">**Approximate Nearest Neighbor (ANN)**</span> search.

```
Exact search:  ████████████████████ 100% scanned → 100% accurate → 🐌 Slow
ANN search:    ███░░░░░░░░░░░░░░░░  ~5% scanned → ~95-99% accurate → ⚡ Fast!
```

<!-- pause -->

**Analogy:** 📦 Finding a delivery address in a city

- **Exact search:** Check every house in every street → hours 🐌
- **With pincode:** Go to the right area, check nearby streets → minutes ⚡
- **The catch:** Might miss a house on the border of two pincodes

<!-- end_slide -->

# Chapter 3: Two Index Strategies

**Two dominant approaches to ANN indexing.**

Let's look at each one...

<!-- end_slide -->

# Strategy 1: IVFFlat — Cluster & Search

<span style="color: #4EC9B0">**IVFFlat**</span> = Inverted File Index with Flat Storage

<!-- column_layout: [1, 1] -->

<!-- column: 0 -->

**Build:** Divide vectors into groups (clusters)

*"Supermarket aisles — dairy, snacks, spices"* 🛒

![](images/gifs/clustering.gif)

<!-- column: 1 -->

**Query:** Search only the nearest group(s)

*"Need butter? Go to dairy aisle, skip the rest"* 🧈

![](images/ivfflat.png)

<!-- end_slide -->

# IVFFlat: How Clustering Works

**Step 1: Group similar vectors into clusters (k-means)**

```
        Y
    1.0 │  ●(0.2,0.9)              ●(0.8,0.95)
        │   "cats are cute"          "neural networks"
    0.8 │  ●(0.15,0.8)              ●(0.85,0.85)
        │   "dog breeds"              "deep learning"
    0.6 │    ⭐(0.18,0.7)            ⭐(0.82,0.75)
        │    Centroid A               Centroid B
    0.4 │  ●(0.25,0.5)              ●(0.75,0.6)
        │   "pet food"                "GPU training"
    0.2 │
        └──────────────────────────────────── X
        0.0                                 1.0
```

<!-- pause -->

**Step 2: Query → find nearest centroid → search only that cluster**

```
Query: "deep learning models" → vector (0.80, 0.78)
  → Nearest centroid: B at (0.82, 0.75)  ✓
  → Search only Cluster B: 3 docs instead of 6!
```

<!-- end_slide -->

# IVFFlat: Why It's Fast

```
6 docs, 2 clusters → searched 3/6 (50%)

At real scale:
  1M docs, 1000 clusters → search ~1000 instead of 1M
  = 1000x fewer comparisons ⚡
```

<!-- pause -->

**Tuning knob:** `nprobe` = how many clusters to check
- `nprobe=1` → fastest, might miss edge cases
- `nprobe=10` → slower, better recall

<!-- end_slide -->

# Strategy 2: HNSW — Multi-Layer Graph

<span style="color: #4EC9B0">**HNSW**</span> = Hierarchical Navigable Small World

Build a navigable graph with layers.
Top layers = express highways. Bottom layer = local streets.

*"GPS navigation — highways first, then local roads to the destination."* 🗺️

![](images/hnsw.png)

<!-- end_slide -->

# HNSW: How the Graph Works

<!-- column_layout: [1, 1] -->

<!-- column: 0 -->

**The structure — zoom levels:**

```
Layer 2 (Express):  A ════════════ D
                    (2 nodes, long jumps)

Layer 1 (Main):     A ─── C ─── D ─── F
                    (4 nodes, medium links)

Layer 0 (All):      A ─ B ─ C ─ D ─ E ─ F
                    (all 6 nodes, dense)
```

<!-- column: 1 -->

**Search for "deep learning":**

```
Layer 2: Start at A
  A ════════════ D
  dist(A)=0.9    dist(D)=0.3 ✓ jump!

Layer 1: At D
  D ─── F
  dist(D)=0.3    dist(F)=0.4
  D still best. Stay.

Layer 0: At D
  D ─ E ─ F
  dist(D)=0.3  dist(E)=0.05 🎯
  → E = best match!
```

<!-- pause -->

*Like GPS: highway to the right area,
then local roads to the exact address.*

<!-- reset_layout -->

![](images/gifs/hnsw-network.gif)

<!-- end_slide -->

# IVFFlat vs HNSW: The Trade-offs

<!-- column_layout: [1, 4, 1] -->

<!-- column: 0 -->

<!-- column: 1 -->

| | IVFFlat | HNSW |
|---|---|---|
| **Speed** | <span style="color: #a6e3a1">Fast (50-100x)</span> | <span style="color: #a6e3a1">Faster (70-150x)</span> |
| **Accuracy** | <span style="color: #f9e2af">~90-95% recall</span> | <span style="color: #a6e3a1">~95-99% recall</span> |
| **Build time** | <span style="color: #a6e3a1">Fast (~30-60s for 50K)</span> | <span style="color: #f9e2af">Slower (~2-5 min for 50K)</span> |
| **Index size** | <span style="color: #a6e3a1">Smaller</span> | <span style="color: #f9e2af">Larger (graph overhead)</span> |
| **Inserts** | <span style="color: #f38ba8">Degrades over time</span> | <span style="color: #a6e3a1">Handles well</span> |

<!-- column: 2 -->

<!-- reset_layout -->

<!-- pause -->

**Rule of thumb:**
- <span style="color: #4EC9B0">**HNSW**</span> for production, user-facing apps (search APIs, chatbots, RAG)
- <span style="color: #4EC9B0">**IVFFlat**</span> for batch jobs, analytics, write-heavy workloads

<!-- end_slide -->

# ⚠️ Critical: Always Use LIMIT!

**Without LIMIT, the database <span style="color: #f38ba8">can't use ANN indexes.</span>**

```sql
-- ❌ BAD: No target K → can't use ANN index
SELECT * FROM docs
ORDER BY distance(embedding, query)

-- ✅ GOOD: LIMIT = top K → ANN index kicks in
SELECT * FROM docs
ORDER BY distance(embedding, query)
LIMIT 10
```

<!-- pause -->

**Why?** ANN indexes are built to find the <span style="color: #f9e2af">top K nearest</span> — they stop early
once they have K good candidates. No K = no early stopping = no index.

*LIMIT here isn't pagination — it's telling the search algorithm "I only need the best 10."*

<!-- pause -->

*Forgetting LIMIT is like ordering everything on the menu just to pick one dish* 🍟

![](images/gifs/fries.gif)

<!-- end_slide -->

# Chapter 4: The Scale Wall

**ANN indexes are fast. But they assume <span style="color: #f38ba8">vectors live in RAM.</span>**

That's fine at 1M vectors. At 100M? Let's do the math.

![](images/gifs/math-lady.gif)

<!-- end_slide -->

# The <span style="color: #f38ba8">RAM</span> Math

*...just the vectors 😳*

```
Per vector:  1536 dims × 4 bytes = 6 KB
```

<!-- column_layout: [1, 4, 1] -->

<!-- column: 0 -->

<!-- column: 1 -->

| Scale | Raw Vectors | + Index Overhead | Approx. RAM Cost |
|-------|------------|-----------------|-----------------|
| 1M | 6 GB | ~9 GB | ~$50/mo |
| 10M | 61 GB | ~92 GB | ~$500/mo |
| 100M | 614 GB | ~920 GB | ~$5,000+/mo |
| 1B | 6.1 TB | ~9.2 TB | 💀 |

<!-- column: 2 -->

<!-- reset_layout -->

![](images/gifs/this-is-fine.gif)

<!-- pause -->

**The cliff isn't linear.** Going from 64 GB → 920 GB means jumping from
a single machine to a distributed cluster.

<span style="color: #f38ba8">That's not 15x cost — it's 30-50x operational complexity.</span>

<!-- end_slide -->

# Two Ways Through the Wall

**Levers to pull:**
1. **Smaller embeddings:** 384 dims = 1.5 KB (4x smaller) — <span style="color: #f9e2af">but lower accuracy without fine-tuning</span>
2. **Quantization:** Compress vectors without losing much accuracy

![](images/two-ways.png)

<!-- end_slide -->

# <span style="color: #f9e2af">Quantization:</span> Compress Smartly

**Core idea:** Full precision isn't needed for *searching*.
Only for the final *ranking* of top candidates.

<!-- column_layout: [1, 1] -->

<!-- column: 0 -->

<span style="color: #4EC9B0">**Scalar Quantization**</span>
```
FP32 → INT8
[0.2341, -0.8912, 0.4563]
         ↓
[60, -228, 117]
```
4x compression. Like JPEG for vectors.

<span style="color: #4EC9B0">**Binary Quantization**</span>
```
Positive → 1, Negative → 0
[0.23, -0.89, 0.45, -0.12]
         ↓
[1, 0, 1, 0]
```
32x compression. Lightning fast (XOR + count).

<!-- column: 1 -->

<span style="color: #f9e2af">**The production pattern:**</span>

```
Query arrives
  ↓
1. Search compressed index (RAM)
   → top 1000 candidates (fast!)
  ↓
2. Fetch full-precision vectors
   for those 1000 only (disk)
  ↓
3. Re-rank with exact distances
   → return true top 10
```

<!-- pause -->

*<span style="color: #f9e2af">Search blurry, rank sharp.</span>*

The blurry copy finds the neighborhood.
The sharp original picks the winner.

<!-- end_slide -->

# 💻 Demo: Quantization — 32x Compression, High Recall

<!-- column_layout: [1, 1] -->

<!-- column: 0 -->

![](images/quantization-blocks.png)

<!-- column: 1 -->

&nbsp;

&nbsp;

**See the transformation:**
```bash
python scripts/quantization_intro.py
```

<!-- pause -->

**See it at scale (10K vectors):**
```bash
python scripts/quantization_demo.py
```

<!-- end_slide -->

# Beyond RAM: <span style="color: #4EC9B0">Disk-Based Indexes</span>

**When even quantization isn't enough, move the index to SSD.**

<!-- column_layout: [1, 1] -->

<!-- column: 0 -->

<span style="color: #4EC9B0">**DiskANN**</span> (used in Serach Engines for that AI answer section):

```
RAM:  Compressed graph + tiny codes
      (~10-25 GB for 100M vectors)
SSD:  Full-precision vectors
      (fetched only for final candidates)
```

<span style="color: #f38ba8">**But aren't disk reads slow?**</span>

<span style="color: #f9e2af">Based on "Six Degrees of Separation" Concept</span>

```
7B people, ~6 hops to reach anyone

You → 🔵 → 🔵 → 🔵 → 🔵 → 🔵 → ✅

Doubling data = ~1 extra hop, not 2x work
```

| Factor | HNSW | Q-HNSW | DiskANN |
|--------|------|--------|---------|
| RAM (100M) | ~920 GB | ~30-60 GB | ~10-25 GB |
| Latency | 1-5ms | 2-8ms | 5-15ms |
| Cost | ~$5K/mo | ~$500/mo | ~$200/mo |

<!-- column: 1 -->

![](images/diskann-query-flow.png)

<!-- reset_layout -->

<!-- pause -->

**The trade-off:** Slightly higher latency, <span style="color: #a6e3a1">massively lower cost.</span>

<!-- end_slide -->

# Chapter 5: Production Reality

<!-- pause -->

**Surprise 1:** Real queries have filters → vector index is blind to `WHERE tenant_id = 42`

<!-- pause -->

**Surprise 2:** Keywords still matter → combine vector + keyword search (hybrid)

<!-- pause -->

**Surprise 3:** <span style="color: #f38ba8">Filtered search fails silently</span> — post-filter returns too few, pre-filter falls back to brute force

*More on filtered search in the bonus section if we have time.*

<!-- end_slide -->

# <span style="color: #a6e3a1">Hybrid Search:</span> Best of Both Worlds

**Vector search finds meaning. Keyword search finds exact terms. Combine them.**

Query: <span style="color: #f9e2af">"how to handle user authentication timeout"</span>

```
Keyword (BM25):  "Authentication timeout error handling guide"
                 → exact match on keywords

Vector search:   "Session expiry and token refresh best practices"
                 → semantically related, different words

Combined → Better recall than either alone
```

<!-- pause -->

Combine with <span style="color: #4EC9B0">Reciprocal Rank Fusion (RRF)</span>:
- *If two friends both recommend the same restaurant, it's probably good* 🍽️

<!-- end_slide -->

# Decision Matrix: What to Use When

<!-- column_layout: [3, 2] -->

<!-- column: 0 -->

| Situation | What to Do |
|---------------|-----------|
| < 1M docs | HNSW on existing DB |
| 1-10M, need filters | Partial indexes / partitioning |
| Cost wall at 10-50M | Quantization (2x-32x) |
| 50M-1B | Disk-based (DiskANN) |
| Keyword + semantic | Hybrid (BM25 + vectors) |
| Sub-5ms at 100M+ | Specialized vector DB |
| Already on Mongo/Elastic | Use native vector support |

<!-- pause -->

**Golden rule:** <span style="color: #a6e3a1">Start with the existing DB.</span>
Migrate only when it's outgrown.

<!-- column: 1 -->

```
Recall
100% │       ●──── Brute force
     │     ●
 98% │   ●        HNSW ef=200
 95% │ ●          HNSW ef=40
 90% │●           IVFFlat
     └──────────────────
     1ms  10ms  50ms  500ms
```

*Pick the trade-off the product needs.*

<!-- end_slide -->

# Key Takeaways

<!-- pause -->

**1. Embeddings are GPS coordinates for meaning.**
   Text → numbers. Similar meaning → nearby numbers. That's the whole trick.

<!-- pause -->

**2. Approximate search is the unlock.**
   Exact results aren't needed. 95-99% accuracy at 100x speed is the right trade-off.

<!-- pause -->

**3. Do the RAM math early.**
   100M × 1536d = 920 GB. Quantization and disk indexes are the escape hatches.

<!-- pause -->

**4. Filtered search is the hidden production trap.**
   Test your real query patterns with filters. Don't assume the index handles it.

<!-- pause -->

**5. Measure recall, not just latency.**
   <span style="color: #f38ba8">A fast wrong answer is worse than a slightly slower right answer.</span>

<!-- end_slide -->

# The End

<!-- column_layout: [2, 1] -->

<!-- column: 0 -->

**<span style="color: #f9e2af">Vectors aren't special. Architecture decisions are.</span>** 🚀

**Questions?**

📬 **Get in touch:**
<span style="color: #89b4fa">jeevan.dc24@alumni.iimb.ac.in</span>

🌐 **I write at** <span style="color: #89b4fa">noobj.me</span>

📎 **Part 2:** `vector_storage_at_scale.md` in the same repo
*(RAM wall, quantization, DiskANN, filtered search — recording coming soon)*

<!-- column: 1 -->

![](images/gifs/thank-you-bow.gif)

<!-- reset_layout -->

<!-- column_layout: [1, 2, 1] -->

<!-- column: 0 -->

<!-- column: 1 -->

**Slides & Code:**

```
█████████████████████████████████████████
██ ▄▄▄▄▄ █  ▄▄ ▄▀   ▀ ▄▀ █▀▄▀█▀█ ▄▄▄▄▄ ██
██ █   █ █▄▀█▀▄ ██▀▀▄▄█ ██▀ ▄ ▀█ █   █ ██
██ █▄▄▄█ █▄▄█▀  ▀▀███▄▀▄▀▀█▀▄█ █ █▄▄▄█ ██
██▄▄▄▄▄▄▄█▄▀▄█▄█ █ ▀ █▄█ ▀▄▀▄▀ █▄▄▄▄▄▄▄██
██ ▀█▄  ▄▄ ▄▄▄█▀ █▀█▀███▀ █▀▄▀ ▄█▀ ▀  ▄██
████  ▀█▄ ▄ ▄▀█▄▄▄ ▀▄  █▀ █▄▀▄ █▄▄▄▀▀▀ ██
███▀ ▀██▄▀▀ ▀ ▄▀▄  █ █▄▀█▀▄▀▀ ▄█▄▄▀ ██▄██
███▄ ▄▄ ▄▄█▀▄██ █▄██▄▄█▄▀▀▄▄   ▄▀▀▄    ██
██ ██ ▄▀▄█ ▄▀▄  ███▄▄██▀ █  █ █ ▄▀█▀▄████
██ ▀▀▄▀▄▄ ▄ ▄█ ▀█▀ ▄█ ▀█▄▄█ █▄  ▀▄█ ██ ██
██ ▀▄▄█ ▄▀▄█▀ ▄█ ▀  ▀ ▄▀ ▀▄▀▀ ▄ ▄▄ █▀████
████▄▄▀▀▄▀  ▀▀▄ ▄▄▀█▀▀███▄▀▄▀▄▄█▀ ▀ ▀█ ██
██ █▀█▄█▄█▀ ▄▀ █▀██ ▀ ▄ ▄ ▄██ ▀█▄▄▀██▄███
██ ▄▄▀▀▀▄█▄ ▀▀▄▄▀▄▀█ ▀███▀██▄▄▀▄ ▀▄▀▀▄▄██
██▄█▄██▄▄█  ▄█▀▀▄ █▀▀  ▀▄▄█▄█  ▄▄▄ ▄ ▀▄██
██ ▄▄▄▄▄ █ ▀█▄ ▄▀ ▀▄▄ █▀█▄▄▀ ▀ █▄█ ███ ██
██ █   █ █   ▀▄██▄▄▀▄▄ ▄▀▀▄▀ ▄   ▄▄██▄ ██
██ █▄▄▄█ ██ ▀█▀█▄▀█ ▄███  ▀█ ▄▄▄▀█ ▀▀▀ ██
██▄▄▄▄▄▄▄█▄▄▄▄████▄██▄▄██▄████▄▄▄▄█▄██▄██
```

<!-- column: 2 -->

<!-- end_slide -->

# Bonus: The <span style="color: #f38ba8">Filtered Search</span> Trap

**In production, almost never searching the entire database:**

```sql
SELECT * FROM products
WHERE tenant_id = 42 AND category = 'electronics'
ORDER BY distance(embedding, query)
LIMIT 10
```

<!-- pause -->

The vector index is blind to `tenant_id` and `category`.

<!-- pause -->

<!-- column_layout: [1, 1] -->

<!-- column: 0 -->

![](images/filtered-search-problem.png)

<!-- column: 1 -->

<span style="color: #f38ba8">**Post-filter:**</span>
```
ANN top 100 → filter → only 2 match!
Asked for 10. Got 2. 😬
```

<span style="color: #f38ba8">**Pre-filter:**</span>
```
Filter to 200 docs → ANN useless
Falls back to brute force.
```

<!-- pause -->

**Solutions:** iterative scanning, partial indexes, partitioning — but <span style="color: #f38ba8">this is the #1 gotcha in production.</span>

<!-- end_slide -->

# Appendix: The Restaurant Analogy (Complete)

<!-- column_layout: [1, 1] -->

<!-- column: 0 -->

**Sequential Scan (Brute Force):**
```
Walk every street, check every building
🚶 → 🏠 → 🏠 → 🏠 → 🏠 → 🍽️

"Is this Italian? No.
 Is this Italian? No..."
Check ALL restaurants one by one
```

**Keyword Search (BM25 / TF-IDF):**
```
Look up in phone book
📖 "Italian" → [Addr1, Addr2, Addr3]
🚗 → 🍽️ (direct jump)

Only visit restaurants
labeled "Italian"
```

<!-- column: 1 -->

**IVFFlat (Cluster Search):**
```
Fly to the Italian district
🚁 → [Downtown] → 🏠 → 🏠 → 🍽️

Search every restaurant in the area
(even non-Italian ones nearby)
```

**HNSW (Graph Navigation):**
```
Highway → Avenue → Street
🛫 → 🚗 → 🚶 → 🍽️

Start at a famous restaurant
Follow recommendations to closer ones
```

<!-- end_slide -->

# Appendix: Recall vs Latency

*Recall = "of the true top 10 results, how many did we actually find?"*

```
Recall
100% │          ●──────────── Brute force (exact)
     │        ●
 98% │      ●                 HNSW ef=200
     │    ●
 95% │  ●                     HNSW ef=40
     │●
 90% │                        IVFFlat probes=1
     └──────────────────────
     1ms   5ms  10ms  50ms  500ms   Latency
```

<!-- pause -->

**The question isn't "best index?" — it's "what does my product need?"**

- Internal chatbot / RAG: 95% recall, < 100ms is fine
- Customer-facing search: 90% recall, < 20ms required
- Fraud / compliance: 99%+ recall, latency doesn't matter

<!-- end_slide -->

# Appendix: Quantization Comparison

| Method | Compression | Recall (w/ re-rank) | Speed | Training? |
|--------|------------|-------------------|-------|-----------|
| FP32 (baseline) | 1x | 100% | 1x | No |
| FP16 (half) | 2x | ~99.9% | ~1.5x | No |
| Scalar INT8 | 4x | ~98-99% | ~2-3x | No |
| Product (PQ) | 8-64x | ~95-99% | ~5-10x | Yes |
| Binary (BQ) | 32x | ~92-96% | ~15-30x | No |

<!-- pause -->

**Start with FP16** (free 2x win, zero recall loss).
**Graduate to BQ + re-rank** when 32x compression is needed.

<!-- end_slide -->

# Appendix: Vector Index Comparison

| | Brute Force | IVFFlat | HNSW | DiskANN |
|---|---|---|---|---|
| **Recall** | 100% (exact) | 90-98% | 95-99.9% | 95-99% |
| **Latency (1M)** | 50-500ms | 2-10ms | 1-5ms | 5-15ms |
| **RAM (100M, 1536d)** | 614 GB | 614 GB | ~920 GB | ~10-25 GB |
| **Build time (1M)** | None | ~30s | ~5 min | ~2 min |
| **Incremental insert** | N/A | Degrades | Yes | Limited |
| **Best for** | < 10K vectors | Batch/analytics | Production | 50M-1B |

<!-- end_slide -->
