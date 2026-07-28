# Handoff: Vector Storage at Scale Talk — OSS Summit Korea

## Event
- **What:** Open Source Summit Korea (Linux Foundation)
- **When:** Aug 11-12, 2026, Seoul
- **Track:** Open AI & Data
- **Duration:** ~30 min
- **Audience:** Open source developers, infra engineers, mixed experience, international (English + Korean)

## Current State

**Active deck:** `vector_storage_at_scale_v3.md` (presenterm format)
**Run with:** `presenterm vector_storage_at_scale_v3.md`
**Export PDF:** `script -q /dev/null bash -c "stty rows 50 cols 200; presenterm vector_storage_at_scale_v3.md --export-pdf -o vector_storage_at_scale_v3.pdf"`

## Files Created This Session

### Learning Files (`learning/`)
| File | Topic |
|------|-------|
| `01-pgvector-08-whats-changed.md` | pgvector 0.8 features (iterative scan, faster HNSW, SIMD) |
| `02-matryoshka-embeddings-mrl.md` | MRL training, cascade pattern, composing with quantization |
| `03-long-context-vs-rag.md` | Cost/latency/recall comparison, decision framework |
| `04-agentic-rag-multi-hop.md` | Query rewriting, multi-hop, self-correcting, Graph RAG |
| `05-observability-recall-drift.md` | Silent quality degradation, golden eval sets, CI/CD gates |
| `06-hybrid-search-maturation.md` | ParadeDB, late chunking, index staleness |
| `07-pgvector-vs-dedicated-dbs.md` | 471 vs 41 QPS benchmark, updated decision matrix |
| `08-opening-slides-draft.md` | Opening slides concept (RAG architecture → scaling focus) |
| `00-talk-outline-30min.md` | Original 30-min outline (superseded by v3 deck) |

### Images Created (`images/`)
| File | What |
|------|------|
| `rag-architecture-decisions.svg/.png` | Full RAG pipeline with "today's focus" highlighted |
| `scaling-path.svg/.png` | 4-stage scaling progression (100K→50M+) |
| `three-levers.svg/.png` | Dimensions → Bits → Disk (3 compression levers) |
| `matryoshka-visual.svg/.png` | Nesting doll shapes with dimension labels |
| `six-degrees-diskann-v2.svg/.png` | Colorful 1-6 chain + globe network |
| `diskann-query-flow.svg/.png` | Query flow: RAM section + NVMe SSD (no text panel) |
| `filtered-search-problem-horizontal.svg/.png` | Pre-filter vs Post-filter (landscape) |
| `filtered-search-fixes.svg/.png` | 3 approaches: iterative/partial/partition |
| `recall-drift-detection.svg/.png` | Dual chart: distance drift + recall decline |
| `benchmark-pgvectorscale-vs-pinecone.svg/.png` | QPS + latency comparison chart |
| `retrieval-pipeline-2023-vs-2026.svg/.png` | 2023 linear vs 2026 agentic loop |
| `tradeoff-mental-model.svg/.png` | 4 slider pairs + product examples + lever impact |
| `decision-matrix.svg/.png` | Scale axis with action boxes + cross-cutting concerns |
| `qr-repo.png` | QR code for github.com/jeevandc/vector-search-talk |
| `six-degrees-people.jpg` | Downloaded reference (small, 500px) |
| `six-degrees-network.jpg` | Downloaded reference (734px) |

### Deck Versions
| File | Status |
|------|--------|
| `vector_storage_at_scale.md` | Original v1 (kept as reference) |
| `vector_storage_at_scale_v2.md` | Intermediate iteration (can delete) |
| `vector_storage_at_scale_v3.md` | **CURRENT ACTIVE DECK** |
| `vector_storage_at_scale_v3.pdf` | Last exported PDF (may be stale, re-export) |

## Narrative Structure (v3)

```
1. RAG Architecture diagram (show complexity, highlight scaling section)
2. Scaling Path (100K → 1-10M → 10-50M → 50M+)
3. Why This Talk (Month 1-10 timeline + gif)
4. Today's Journey (4 items)
5. How Do Computers Compare Text (fries example + mind-blown gif)
6. Why Vector Indexing Is Different (B-tree vs vectors)
7. HNSW (how ANN works)
8. The RAM Wall (table + this-is-fine gif)
9. Cost of Getting It Wrong (3 patterns + interstellar gif)
10. Three Ways Through the Wall (3 levers image)
11. Lever 1: Matryoshka (nesting dolls image)
12. Lever 2: Quantization (quantization-blocks image)
13. Demo: Quantization
14. Lever 3: DiskANN (six degrees image)
15. DiskANN Architecture (flow image + text columns)
16. Silent Failure #1: Filtered Search
17. Pre-Filter vs Post-Filter (horizontal image)
18. The Fixes (3 approaches image)
19. Filtered Search: What to Use When (table)
20. Silent Failure #2: Recall Drift
21. Detecting Drift: Two Flows (chart image)
22. Is a separate vector DB needed? (architecture-decision image)
23. The 2026 Answer (benchmark image)
24. The Data Sync Tax (image)
25. Long Context vs RAG (table)
26. When to Use Which (columns)
27. Hybrid Search: concept
28. Hybrid Search: ParadeDB stack
29. Retrieval Pipeline 2026 (agentic RAG image)
30. Trade-off Mental Model (sliders image)
31. Decision Matrix (visual image)
32. The End (QR + links)
33-47. Appendix slides
```

## Key Decisions Made

1. **v1 as base** — kept visual DNA, diagrams, gifs, column layouts
2. **OSS Summit framing** — emphasize open source tools + licenses, no vendor pitch
3. **Opening with RAG architecture** — show full complexity, zoom into scaling section
4. **Three walls narrative** — RAM wall, silence wall, complexity wall
5. **MRL before quantization** — "reduce dimensions first" is the new first lever
6. **Filtered search as "Silent Failure #1"** — paired with recall drift as #2
7. **pgvector benchmark** — 471 vs 41 QPS (Timescale data)
8. **Long context vs RAG** — addressed as 1 slide (earns trust)
9. **Agentic RAG** — "pipeline changed, DB doesn't need to" framing
10. **Trade-off mental model** — 4 slider pairs, broader than just recall vs latency
11. **Decision matrix as image** — visual flowchart, not text table
12. **Handout** — `rag-system-decision-checklist.md` (30 sections) as companion

## Known Issues / TODO

### Images to Source (need high-res, manual download)
- **Matryoshka dolls real photo** — current SVG has doll shapes but a real photo would be more impactful. Source from Unsplash/stock (1200px+ wide). Save as `images/matryoshka-dolls-real.jpg`
- Alternatively: the current SVG doll shapes at 16:9 work fine

### Presenterm Rendering Limitations
- Images render at native resolution — can't upscale beyond pixel size
- GIFs are limited by their source resolution (flipping-papers.gif is 480×304)
- SVGs must be converted to PNG (presenterm doesn't support SVG directly)
- `<!-- -->` comments are interpreted as commands — can't use HTML comments
- Emojis in SVGs don't render (rsvg-convert lacks emoji font) — use text labels

### Content Decisions Still Open
- **Demo: Quantization** — keep or cut depending on time during rehearsal
- **Appendix slides** — may need pruning if deck feels too long
- **QR code URL** — update `github.com/jeevandc/vector-search-talk` with actual repo
- Consider adding speaker notes in a separate file for rehearsal

### Potential Improvements
- Source higher-res gifs (flipping-papers, mind-blown) for bigger rendering
- Create a proper visual for "Today's Journey" (timeline/roadmap image instead of bullets)
- The "Long Context vs RAG" table slide could become a visual comparison image
- Consider a "What to Do Monday Morning" closing slide (was removed — decision matrix may cover it)

## How to Re-export PDF

```bash
cd /Users/Jeevan.Chikkegowda/labs/hacks/pgvector-data-storage-talk
script -q /dev/null bash -c "stty rows 50 cols 200; presenterm vector_storage_at_scale_v3.md --export-pdf -o vector_storage_at_scale_v3.pdf"
```

## How to Regenerate an SVG→PNG

```bash
# All custom images are in images/*.svg with matching .png
rsvg-convert -w 2400 images/FILENAME.svg -o images/FILENAME.png
```

## Companion Materials
- `rag-system-decision-checklist.md` (at ~/rag-system-decision-checklist.md) — 30-section handout
- Push both the deck + checklist to the repo for the QR code to work
