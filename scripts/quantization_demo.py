#!/usr/bin/env python3
"""Quantization at scale — measured small, estimated large.

Best of both:
  - SMALL index: we actually embed real sentences with MiniLM, quantize them,
    and report the MEASURED byte size and MEASURED recall@10.
  - LARGE index (1M / 10M / 100M): we don't build these (100M FP32 = 154 GB,
    won't fit in RAM). RAM is exact extrapolation (bytes/vector x N); recall is
    a typical published estimate for binary quantization + fixed re-rank.

Vectors are 384-d (all-MiniLM-L6-v2). A 1536-d model (OpenAI/Cohere-scale) is
4x these RAM numbers — the wall is worse, the argument stronger.

No database, no network after the model is cached (first run downloads ~90 MB).
"""

import os, warnings, logging, time
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import numpy as np

TOP_K = 10
N_QUERIES = 50
BQ_RERANK_K = 200
SQ_RERANK_K = 100
SEED = 42

TOPICS = {
    "login": ["I can't log into my account", "how do I reset my password",
        "forgot my password and can't sign in", "the login page rejects my credentials",
        "steps to recover my account access", "my password reset email never arrived",
        "locked out after too many login attempts"],
    "billing": ["I was charged twice this month", "there's an unexpected fee on my invoice",
        "why is my bill higher than usual", "I see a duplicate charge on my card",
        "please explain these billing charges", "my subscription price went up",
        "requesting a breakdown of my latest invoice"],
    "refund": ["I want a refund for my last order", "how do I get my money back",
        "requesting a refund for a defective product", "the item arrived damaged, I need a refund",
        "please reverse the charge and refund me", "how long does a refund take",
        "I returned the item but haven't been refunded"],
    "shipping": ["where is my package", "my order hasn't arrived yet", "the delivery is delayed",
        "tracking shows no movement for days", "when will my shipment be delivered",
        "the courier marked it delivered but I didn't receive it", "how do I change my shipping address"],
    "bug": ["the app crashes on startup", "the application keeps freezing",
        "I found a bug in the checkout flow", "the screen goes blank when I tap save",
        "the app closes unexpectedly", "there's an error message when I open the app",
        "the feature stopped working after the update"],
    "performance": ["the app is really slow", "pages take forever to load", "the dashboard is laggy",
        "search results are very slow to appear", "the site performance has degraded",
        "everything is sluggish since the last release", "response times are unacceptably high"],
    "cancel": ["I want to cancel my subscription", "how do I unsubscribe", "please cancel my plan",
        "I'd like to end my membership", "stop my recurring billing",
        "cancel my account renewal", "how to terminate my subscription"],
    "feature": ["can you add dark mode", "please support exporting to CSV",
        "it would be great to have a mobile widget", "I'd love an option to schedule reports",
        "please add multi-language support", "a bulk edit feature would help",
        "consider adding keyboard shortcuts"],
    "export": ["how do I export my data", "I need to download all my records",
        "can I get a full data dump", "export my history to a spreadsheet",
        "how to back up my account data", "I want a copy of everything I've stored",
        "is there an API to export my data"],
    "security": ["I think my account was hacked", "there is suspicious activity on my account",
        "I received a strange login alert", "is my data safe after the breach",
        "someone accessed my account without permission", "how do you protect my personal data",
        "I want to report a security concern"],
    "api": ["how do I authenticate with the API", "the API returns a 401 error",
        "where are the API docs", "how to integrate your service with our backend",
        "the webhook isn't firing", "rate limits on the API are unclear",
        "sample code for calling the REST endpoint"],
    "account": ["how do I change my email address", "update my profile information",
        "I want to delete my account", "how to change my username",
        "merge two accounts into one", "update my notification preferences",
        "how do I close my account permanently"],
}
PREFIXES = ["", "Customer says: ", "Ticket: ", "Urgent: ", "Hi team, "]
SUFFIXES = ["", " Please help.", " Thanks."]


def build_corpus():
    out = []
    for phrasings in TOPICS.values():
        for base in phrasings:
            for pre in PREFIXES:
                for suf in SUFFIXES:
                    s = pre + base + suf
                    out.append(s[0].upper() + s[1:])
    return out


def binary_quantize(vecs):
    return np.packbits((vecs > 0).astype(np.uint8), axis=1)


def scalar_quantize(vecs):
    """FP32 -> UINT8 per dimension (4x smaller)."""
    vmin, vmax = vecs.min(axis=0), vecs.max(axis=0)
    scale = vmax - vmin; scale[scale == 0] = 1
    return ((vecs - vmin) / scale * 255).astype(np.uint8), vmin, scale


def exact_topk(vecs, query, k):
    return np.argpartition(-(vecs @ query), k)[:k]


def hamming_topk(bq_vecs, bq_query, k):
    dist = np.unpackbits(np.bitwise_xor(bq_vecs, bq_query), axis=1).sum(axis=1)
    return np.argpartition(dist, k)[:k]


def fmt(b):
    for lim, unit in ((1e12, "TB"), (1e9, "GB"), (1e6, "MB"), (1e3, "KB")):
        if b >= lim:
            return f"{b/lim:.1f} {unit}"
    return f"{b:.0f} B"


def label(n):
    if n >= 1_000_000: return f"{n//1_000_000}M"
    if n >= 1_000: return f"{n//1_000}k"
    return str(n)


def run():
    from sentence_transformers import SentenceTransformer
    rng = np.random.default_rng(SEED)

    print("=" * 84)
    print("  QUANTIZATION AT SCALE — measured on 1k real vectors, estimated at scale")
    print("=" * 84)

    sentences = build_corpus()
    print(f"\nEmbedding {len(sentences):,} REAL sentences with all-MiniLM-L6-v2...")
    import io, contextlib
    with contextlib.redirect_stderr(io.StringIO()):
        model = SentenceTransformer("all-MiniLM-L6-v2")
    t0 = time.time()
    emb = model.encode(sentences, batch_size=64, normalize_embeddings=True,
                       show_progress_bar=False).astype(np.float32)
    dims = emb.shape[1]
    print(f"  {emb.shape[0]:,} x {dims} real embeddings in {time.time()-t0:.1f}s")

    # --- MEASURED: real embeddings, actual recall@10 for each method ---
    idx = rng.permutation(len(emb))
    q_idx, db_idx = idx[:N_QUERIES], idx[N_QUERIES:]
    vecs, queries = emb[db_idx], emb[q_idx]
    n0 = len(vecs)
    sq, vmin, scale = scalar_quantize(vecs)
    bq, bq_q = binary_quantize(vecs), binary_quantize(queries)

    sq_r, only_r, rr_r = [], [], []
    for i in range(N_QUERIES):
        gt = set(exact_topk(vecs, queries[i], TOP_K))
        sqq = ((queries[i] - vmin) / scale * 255).astype(np.float32)
        cand = np.argsort(-(sq.astype(np.float32) @ sqq))[:SQ_RERANK_K]
        sq_top = cand[np.argsort(-(vecs[cand] @ queries[i]))[:TOP_K]]
        sq_r.append(len(set(sq_top) & gt) / TOP_K)
        only_r.append(len(set(hamming_topk(bq, bq_q[i], TOP_K)) & gt) / TOP_K)
        bcand = hamming_topk(bq, bq_q[i], BQ_RERANK_K)
        b_top = bcand[np.argsort(-(vecs[bcand] @ queries[i]))[:TOP_K]]
        rr_r.append(len(set(b_top) & gt) / TOP_K)
    measured = {"sq": np.mean(sq_r), "only": np.mean(only_r), "rr": np.mean(rr_r)}

    # rows: (name, bytes/vec, measured recall@1k, estimated recall@scale)
    rows = [
        ("FP32 (baseline)",        dims * 4,  1.0,             "100%"),
        ("Scalar INT8  (4x) + rr", dims,      measured["sq"],  "~99%"),
        ("Binary 1-bit (32x)",     dims // 8, measured["only"],"~10%"),
        ("Binary + re-rank",       dims // 8, measured["rr"],  "~92-96%"),
    ]

    print(f"\n  {'Method':<22}{'B/vec':>6}{'R@10 (1k)*':>12}{'RAM @1M':>10}{'RAM @100M':>11}{'R@10 @scale**':>15}")
    print(f"  {'-' * 76}")
    for name, bpv, mr, est in rows:
        print(f"  {name:<22}{bpv:>6}{mr:>11.1%}{fmt(bpv*1_000_000):>10}"
              f"{fmt(bpv*100_000_000):>11}{est:>15}")

    print(f"\n  *  measured on {n0:,} real MiniLM vectors ({dims}-d).")
    print(f"  ** typical published recall at scale (fixed re-rank budget), NOT measured.")
    print(f"  At 100M: FP32 {fmt(dims*4*100_000_000)} won't fit in RAM (the wall); "
          f"binary {fmt(dims//8*100_000_000)} does.  (1536-d models are ~4x this.)")
    print("=" * 84)


if __name__ == "__main__":
    run()
