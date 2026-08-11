# Speaker Notes: Vector Search, Basics to Scale

## Demo preflight

```bash
source venv/bin/activate
python scripts/compare.py    # type q after model loads
python scripts/quantization_demo.py
```

Keep both in shell history. Bump terminal font. Silence notifications.

---

## 1. Title

- "Path from prototype to production that stays affordable and correct."
- Beat after "correct." →

## 2. What Is RAG?

- Point at retrieval step. "Today = this box only. Not prompting, not generation."
- → "That retrieval box looks small, but every box around it hides a choice."

## 3. A RAG System: Every Box Is a Decision

**SKIP IF RUNNING LONG**

- Don't explain every label. One sentence: "Each box can affect quality, latency, and cost."
- → "Those choices get more expensive as the corpus grows."

## 4. The Scaling Path

**SKIP IF RUNNING LONG**

- Talk over GIFs fast. Joke: "Fourth image is also an architecture diagram."
- Let fire gif get a laugh.
- → "Here's the same journey with months attached."

## 5. Why This Talk, Why Now

- Walk the timeline. The killer combo = scale + filters + unmeasured recall.
- Month 10 = sync two databases forever.
- → "We need enough fundamentals to understand the failure, then enough math to avoid it."

## 6. What We'll Cover

- One breath: embeddings, ANN, RAM wall, three levers, silent failures, decision matrix.
- Promise: "I won't skip silent failures — they produce no error message."
- → "Let's see what semantic similarity looks like."

## 7. Demo: compare.py — ~6:45

```
HIGH:    "cancel my subscription" / "I want to unsubscribe"     → ~68%
LOW:     "the bank is closed for the holiday" / "the river bank was steep and muddy" → ~26%
GOTCHA:  "I love pizzas" / "I hate pizzas"                      → ~82%
```

- Before GOTCHA: ask audience "Higher or lower than 68%?" Wait. Reveal ~82%.
- Punchline: "Similarity ≠ agreement. It captures topic, not sentiment."
- If demo stalls: talk through slide results, don't debug on stage.
- → "What did the model create that made those comparisons possible?"

## 8. How Do Computers Compare Text?

- "Computers see different strings. The model turns sentences into coordinates."
- GPS analogy verbally if needed, don't over-explain dimensions.
- → "Once text becomes coordinates, we need a way to measure nearby."

## 9. How Do We Measure 'Close'?

- 2D picture = intuition. Same math in 384 dimensions.
- "`<=>` in PostgreSQL = cosine distance. Smaller = closer."
- → "Measuring one distance is easy. Measuring against every stored vector is the problem."

## 10. Transition: No Sort Order

- "A normal index relies on ordering. Vectors don't give us left-to-right."

## 11. Why Vector Indexing Is Different

- B-trees exploit ordering + binary search. Vectors have no useful "less than."
- Exact = correct but slow at scale.
- → "So vector search makes a deliberate trade."

## 12. The Key Insight: Approximate Is Good Enough — ~12:00

- Define recall@10: "Of the exact top ten, how many did ANN find?"
- Quick audience poll: "Would your product notice one different result in top ten?"
- → "HNSW gets that speed by building shortcuts."

## 13. How ANN Indexes Work — ~12:25

- Talk over image. Large hops → finer layers → local neighborhood.
- Seoul-to-Sokcho once, then move on.
- Key point: "Works great when hot set fits in RAM."
- → "Those shortcuts take memory, and memory is where it gets uncomfortable."

## 14. Transition: The RAM Wall

- "Fast graph traversal is great until the working set outgrows affordable memory."

## 15. The RAM Wall — ~14:30

- **Bridge:** "Demo used 384d. Production models use 1536d — four times larger. This is production math."
- 1536 × 4 bytes ≈ 6 KB per vector. 100M = 614 GB raw. +HNSW ≈ 920 GB.
- Pause after "614 GB raw." Let it land.
- → "HNSW isn't the mistake. Choosing it without this arithmetic is."

## 16. The Cost of Getting It Wrong

**SKIP IF RUNNING LONG**

- Three forms of debt: oversized memory, second data system, rebuild freeze.
- "The tools aren't bad. The sequence of decisions is."
- → "Before adding another database, pull three compression levers."

## 17. Three Ways Through the Wall

- Order matters: dimensions first, then bits, then disk.
- Full vectors stay on SSD for reranking.
- → "First lever: do we need every dimension for every search?"

## 18. Matryoshka Dolls Photo — ~16:30

**SKIP IF RUNNING LONG**

- Talk over the dolls. "Smaller doll is still recognizable. Smaller embedding is still useful."
- → "The condition: model must be trained for truncation."

## 19. Matryoshka Embeddings (MRL)

- 256d prefix stays useful from a 1536d model IF trained for it.
- Not safe for every model. Test recall on labeled set.
- → "Dimensions = how many values. Quantization = how many bits per value."

## 20. Lever 2: Quantization

- FP32 = full precision. Lower bits = rougher approximation.
- Safe pattern: compressed for search, full-precision for rerank.
- → "Several ways to compress, with different tradeoffs."

## 21. Lever 2: The Details

**SKIP IF RUNNING LONG**

- Talk over blocks, don't read them. FP16/scalar/product/binary.
- "No recall percentage is universal."
- → "Let's see what compression does on real vectors."

## 22. Demo: quantization_demo.py — ~21:40

```bash
python scripts/quantization_demo.py
```

- Point to binary-only row (low recall). Wait.
- Point to binary+rerank. "The recovery is the reveal."
- Honest note: "Small corpus = optimistic recall. At 1M+ expect ~92-96% with rerank."
- If stalls: use slide table.
- → "Compression shrinks hot data. DiskANN changes which data needs to stay hot."

## 23. Lever 3: DiskANN

**SKIP IF RUNNING LONG**

- Six-degrees = memory aid, not a guarantee.
- → "Map that graph onto RAM and SSD."

## 24. DiskANN Architecture — ~24:00

- Compact navigation in RAM, vectors on SSD, fetch + rerank.
- Trade: SSD latency for much lower RAM demand.
- → "Cost is visible. The more dangerous failures produce no alarm."

## 25. Transition: Silent Failures — ~24:10

- "The system can be fast, green on the dashboard, and still wrong."

## 26. Silent Failure #1: Filtered Search — ~25:35

- ANN examines limited candidates. Selective filter throws most away.
- "Asked for 10. Got 0. No error. No warning. No log line."
- Pause. Let that discomfort sit.
- → "Pre or post filter — both orderings have tradeoffs."

## 27. Pre-Filter vs Post-Filter

**SKIP IF RUNNING LONG** (fold into 26 and 28 verbally)

- Post = throws away ANN candidates. Pre = fragmented search space.
- "No universal ordering. Benchmark real selectivity."
- → "Even after filters work, quality can drift."

## 28. Silent Failure #2: Recall Drift — ~28:00

- 🦑 "Squid Game rules: you moved and didn't notice she was watching."
- Service stays up, returns rows. Rows are increasingly wrong.
- Pause after "It just quietly becomes useless."
- → "A green health check can't catch this. We need a quality check."

## 29. Detecting Drift — ~29:30

- Two flows: live distance canary (fast but no recall measurement) + golden eval set (slow but real recall@10).
- Run eval when corpus/model/filters/index change.
- → "Once we measure cost, latency, and recall, the decision gets less emotional."

## 30. Trade-off Mental Model — ~31:00

**SKIP IF RUNNING LONG**

- Talk over image. "Every design spends RAM, SSD latency, build time, ops complexity, and recall."
- → "Use those constraints as questions, not product slogans."

## 31. Decision Matrix — ~33:30

- Don't read every cell. Walk the sequence:
  1. Calculate bytes/vector and hot working set
  2. Test HNSW with real filters
  3. Test dimensionality reduction (only if model supports it)
  4. Test quantized search + full-vector rerank
  5. Disk-based ANN when RAM cost fails
  6. Separate vector system only when measured evidence justifies sync cost
- Give audience 5 seconds to photograph the matrix.
- → "This brings us back to Month 10."

## 32. The End — ~35:00

- Deliver slowly: **"Remember Month 10? You don't have to get there."**
- STOP. Let callback land.
- Then: "Do the math early. Choose compression before the bill forces it. Monitor recall from day one."
- Point to QR after message lands.
- "Thank you. Questions?"

---

## Q&A pocket answers

- **384d vs 1536d?** Demos = 384d MiniLM (fast, local). RAM Wall = 1536d production (OpenAI/Cohere). 4× difference.
- **920 GB?** Raw = 614 GB. Slide adds illustrative HNSW overhead.
- **Binary recall 10% or 92-96%?** Binary-only = poor. +Rerank = recovers most. Measure on real corpus.
- **HNSW must fit in RAM?** Best when hot set does. Measure latency under memory pressure.
- **pgvector only fetches 10 then filters?** No — uses candidate budget. Selective filters can exhaust it.
- **Separate vector DB?** Only if workload evidence (QPS, latency SLO, recall, filtering, tenancy, ops) justifies sync cost.
- **recall@10?** Fraction of exact top-10 recovered by ANN top-10.
