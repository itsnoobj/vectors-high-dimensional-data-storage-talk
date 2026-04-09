# Vector Search with PostgreSQL

Two talks on vector search: from fundamentals to production-scale architecture decisions.

## 📖 Talks

| Talk | File | Duration | Audience |
|------|------|----------|----------|
| **Inside pgvector** | `pgvector_presentation.md` | ~20 min | How PostgreSQL stores, indexes & manages high-dimensional data |
| **Vector Search Fundamentals** | `vector_search_fundamentals.md` | ~20 min | Getting started with pgvector — embeddings, indexing, semantic search |
| **Storing High-Dimensional Data at Scale** | `vector_storage_at_scale.md` | ~20 min | Senior/architect — RAM wall, quantization, filtered search, DiskANN, architecture trade-offs |

## 🚀 Quick Start

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your PostgreSQL credentials

# Generate demo data (50k docs, 1024d embeddings, ~10-15 min)
python scripts/generate_demo_embeddings.py

# Run a talk
presenterm vector_search_fundamentals.md
presenterm vector_storage_at_scale.md
```

## 📁 Structure

```
├── images/                              # Presentation images & gifs
├── scripts/
│   ├── generate_demo_embeddings.py      # Main data generator (50k docs)
│   ├── embedding_intro.py              # Embedding basics demo
│   ├── quantization_demo.py            # BQ compression + recall demo
│   ├── ram_wall_calculator.py          # RAM cost calculator
│   └── ...                             # Additional demo scripts
├── vector_search_fundamentals.md        # Talk 1: Fundamentals
├── vector_storage_at_scale.md           # Talk 2: Scale & architecture
├── DEMO_COMMANDS.md                     # SQL commands for live demos
└── .env.example                         # DB config template
```

## 🔧 Configuration

Create `.env` file:
```bash
DATABASE_URL=postgres://user:password@localhost:5432/dbname
```

## 🎥 Presenter

Talks use [presenterm](https://github.com/mfontanini/presenterm). Install with:
```bash
cargo install presenterm
# or
brew install presenterm
```
