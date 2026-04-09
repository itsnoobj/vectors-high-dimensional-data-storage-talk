# Demo Commands

All commands needed to run the demos for the presentation.

## 1. Start PostgreSQL with pgvector

```bash
docker run -d --name pgvector-demo \
  -e POSTGRES_PASSWORD=mysecret \
  -p 5432:5432 \
  -v pgvector-data:/var/lib/postgresql/data \
  pgvector/pgvector:pg17
```

## 2. Setup environment

```bash
cd ~/labs/entain/temp/pgvector-data-storage-talk
echo 'DATABASE_URL=postgres://postgres:mysecret@localhost:5432/postgres' > .env
source venv/bin/activate
pip install -r requirements.txt psycopg2-binary
```

## 3. Generate 50K demo embeddings (one-time, ~10-15 min)

```bash
python scripts/generate_demo_embeddings.py
```

## 4. Python demos (no DB needed)

```bash
# Slide 2: Embedding intro
python scripts/embedding_intro.py

# Slide 9: Quantization demo
python scripts/quantization_demo.py

# Reference only (not in talk):
python scripts/ram_wall_calculator.py
```

## 5. SQL demos (connect with pgcli)

```bash
pgcli postgres://postgres:mysecret@localhost:5432/postgres
```

### Add metadata to docs (run once before filtered search demo)

```sql
UPDATE docs SET metadata = jsonb_build_object(
  'tenant_id', (id % 100),
  'category', CASE (id % 5)
    WHEN 0 THEN 'science' WHEN 1 THEN 'sports'
    WHEN 2 THEN 'politics' WHEN 3 THEN 'tech' ELSE 'culture' END
);
```

### Create HNSW index

```sql
SET maintenance_work_mem = '512MB';
CREATE INDEX docs_hnsw_idx ON docs USING hnsw (embedding vector_cosine_ops);
ANALYZE docs;
```

### Filtered search with iterative_scan (slide 16)

```sql
SET hnsw.iterative_scan = relaxed_order;

EXPLAIN ANALYZE
SELECT id, left(content, 50),
  embedding <=> (SELECT embedding FROM docs WHERE id = 97) AS dist
FROM docs
WHERE metadata->>'category' = 'science'
ORDER BY embedding <=> (SELECT embedding FROM docs WHERE id = 97)
LIMIT 10;
```

### Partial index demo (slide 15)

```sql
CREATE INDEX docs_hnsw_science ON docs
  USING hnsw (embedding vector_cosine_ops)
  WHERE metadata->>'category' = 'science';

SET enable_seqscan = off;

EXPLAIN ANALYZE
SELECT id, left(content, 50),
  embedding <=> (SELECT embedding FROM docs WHERE id = 97) AS dist
FROM docs
WHERE metadata->>'category' = 'science'
ORDER BY embedding <=> (SELECT embedding FROM docs WHERE id = 97)
LIMIT 10;
```

## 6. Present

```bash
presenterm vector_storage_at_scale.md
```

## 7. Cleanup

```bash
docker stop pgvector-demo && docker rm pgvector-demo
docker volume rm pgvector-data
```
