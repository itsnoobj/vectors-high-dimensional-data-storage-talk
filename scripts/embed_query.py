#!/usr/bin/env python3
"""Embed a sentence and print the vector — ready to paste into SQL."""
import sys, os, warnings, logging, io, contextlib
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["MLX_VERBOSE"] = "0"
from sentence_transformers import SentenceTransformer

query = sys.argv[1] if len(sys.argv) > 1 else "how to find and fix slow queries"
with contextlib.redirect_stderr(io.StringIO()):
    model = SentenceTransformer('all-MiniLM-L6-v2')
emb = model.encode(query)

print(f"\n🔍 \"{query}\"\n")
print(f"📐 Vector ({len(emb)} dims, first 5): [{', '.join(f'{v:.4f}' for v in emb[:5])}, ...]")
print(f"\n📋 Copy-paste for SQL:\n")
print(f"'[{','.join(f'{float(v):.8f}' for v in emb)}]'")
