# Speaker Notes & Jokes — Vector Storage at Scale v3

Delivery tips: These are natural one-liners to drop while transitioning or pausing. Don't read them — land them casually like you just thought of it.

---

## Slide: A RAG System: Every Box Is a Decision
> "This diagram has more boxes than my apartment in Seoul. And every box is a decision someone made at 2am before a deadline."

---

## Slide: The Scaling Path
> "100K vectors? That's a weekend project. 100M vectors? That's a performance review."

---

## Slide: Why This Talk, Why Now (Month 1→10)
> "Month 1: 'This is so easy!' Month 10: 'Who approved this architecture?' — same person, by the way."

> "This is basically the five stages of grief, but for infrastructure engineers."

---

## Slide: How Do Computers Compare Text?
> "Computers look at 'I love fries' and 'Fries are great' and go: 'These share exactly zero bytes in common. Completely unrelated.' — and that's why we can't have nice things."

---

## Slide: Why Vector Indexing Is Different
> "B-trees: 'Is this bigger or smaller? Left or right.' Vectors: 'Is this... close? In 1536 dimensions? ...I need a minute.'"

---

## Slide: How ANN Works (HNSW)
> "HNSW is basically Google Maps for vectors. 'Take the highway to the general area, then switch to local streets.' Except the highway has 1536 lanes."

---

## Slide: The RAM Wall
> "When your vector index costs more per month than your senior engineer... it's time to have a conversation."

> "The jump from 10M to 100M is like the difference between 'we need a bigger instance' and 'we need a bigger budget meeting.'"

---

## Slide: The Cost of Getting It Wrong (🦑 Squid Game)
> "In Squid Game, make the wrong choice and you're eliminated. In vector search, make the wrong choice and your budget is eliminated. Same energy."

> "Pattern #3: 'We'll optimize later.' — the 'I'll start the diet Monday' of engineering."

---

## Slide: Three Ways Through the Wall
> "920 GB to 5 GB. That's not compression, that's Marie Kondo for vectors. 'Does this float32 spark joy? No? Binary it is.'"

---

## Slide: Lever 1: Matryoshka Embeddings
> "Matryoshka embeddings: the only time in engineering where making things smaller actually makes them more elegant, not more fragile."

> "It's like Russian nesting dolls — the big one knows everything, the small one still knows enough to find the right neighborhood."

---

## Slide: Lever 2: Quantization
> "FP32 to binary is like going from a full orchestra to someone humming the tune. Surprisingly, you can still recognize the song."

---

## Slide: Demo: Quantization in Action
> "Let's see if turning our vectors into ones and zeros actually works. This is the 'trust the math' moment."

> [After showing results] "10% recall without rerank. That's not a search engine, that's a random number generator with extra steps."

---

## Slide: Lever 3: DiskANN (Six Degrees)
> "Six degrees of separation — works for Kevin Bacon, works for vectors. 'I don't know that vector personally, but my friend's friend's friend does.'"

---

## Slide: DiskANN Architecture
> "$200 a month versus $5,000 a month. Same recall. That's not an optimization, that's a promotion-worthy decision."

> "The trick: keep the address book in RAM, keep the actual documents on SSD. Like remembering where you parked without memorizing the entire parking garage."

---

## Slide: Silent Failure #1: Filtered Search (🦑 Red Light)
> "Red light, green light — except with filtered search, you're always on red light and nobody told you."

> "This is the scariest bug in production: no error, no log, no alert. Just a user staring at an empty page wondering if the internet is broken."

---

## Slide: Pre-Filter vs Post-Filter
> "Pre-filter: 'Search only tenant 42's vectors.' Great in theory. Except HNSW doesn't know what a tenant is. It's like asking Google Maps to only show roads in district 42 — the map doesn't have districts."

---

## Slide: Filtered Search: What to Use When
> "This table looks simple. I assure you, implementing it is not. Ask me about partition maintenance during Q&A if you want to see a grown engineer cry."

---

## Slide: Silent Failure #2: Recall Drift
> "Recall drift is the vector search equivalent of slowly going deaf. You don't notice until someone asks 'didn't you hear me?' and you realize the answer is no."

> "Month 1: 96% recall. Month 9: 84%. The users noticed at month 7. Engineering noticed at month 9. Classic."

---

## Slide: The 2026 Answer: Probably Not
> "Is a separate vector DB needed? 2023: 'probably yes.' 2026: 'probably not.' 2027: someone will give a talk saying 'definitely maybe.'"

> "These are Timescale's numbers, so take them with a grain of salt — but even halving the improvement, it's still compelling."

---

## Slide: The Data Sync Tax
> "Two databases means two sources of truth. Which means zero sources of truth. That's just math."

---

## Slide: Hybrid Search: BM25 + Vectors
> "Vector search is like a really smart friend who understands context but can't remember exact names. BM25 is like that friend who remembers every word but has no idea what anything means. Together? Unstoppable."

---

## Slide: The Retrieval Pipeline Has Changed (2026)
> "2023: one shot, pray it works. 2026: the LLM argues with itself three times before answering. We've successfully taught computers to overthink."

> "The good news: your database doesn't need to be smarter. The bad news: everything above it got way more complicated."

---

## Slide: The Trade-off Mental Model
> "Every decision is a slider. Product managers want all sliders maxed. Physics says no. This is the conversation."

> "If someone tells you they have high recall, low latency, low cost, AND simplicity — they're either lying or they have 10,000 vectors."

---

## Slide: Decision Matrix
> "This is the slide you screenshot and send to your tech lead when they ask 'should we switch to Pinecone?'"

---

## Slide: The End
> "Remember: measure recall under real filters before buying another database. That's it. That's the talk. Everything else was context."

> "감사합니다! If you remember one thing: compress first, measure second, panic never."

---

## General heckle responses:
- "But what about [other vector DB]?" → "If you can prove it's 10x better on YOUR workload with YOUR filters, go for it. Most can't."
- "What about GPU-accelerated search?" → "Great if you already have GPUs. Expensive if you're buying them just for search. Check the appendix."
- "Isn't pgvector slow?" → "It was. pgvector 0.7+ with HNSW is a different product than pgvector 0.4. Benchmarks don't lie."
