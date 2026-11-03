from __future__ import annotations

import csv, hashlib, os, re
from decimal import Decimal
from pathlib import Path
from .core import Product, Promotion, sale_price, installments

SCHEMA = Path(__file__).resolve().parents[1] / "db" / "schema.sql"

def source_data_dir(root: Path) -> Path:
    matches = [p for p in root.glob("*/data") if (p / "desafio_tecnico_ai_eng - products.csv").exists()]
    if not matches: raise FileNotFoundError("Source CSV directory not found")
    return matches[0]

def rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle: return list(csv.DictReader(handle))

def connect():
    try: import psycopg
    except ImportError as exc: raise RuntimeError("Install PostgreSQL support with: pip install -e '.[postgres]'") from exc
    url = os.getenv("DATABASE_URL")
    if not url: raise RuntimeError("DATABASE_URL is required for PostgreSQL commands")
    return psycopg.connect(url)

class PostgresStore:
    """Production data backend used by the same bounded tools as the local mock."""
    def __init__(self): self.conn = connect()
    def close(self): self.conn.close()
    def search_products(self, budget=None):
        with self.conn.cursor() as cur:
            cur.execute("SELECT product_id,name,price_brl,stock_quantity,status,category_id FROM products WHERE status=%s AND stock_quantity>0 AND (%s IS NULL OR price_brl<=%s) ORDER BY name LIMIT 20", ("active", budget, budget))
            return [Product(r[0], r[1], Decimal(r[2]), r[3], r[4], r[5]) for r in cur.fetchall()]
    def get_product(self, product_id):
        with self.conn.cursor() as cur:
            cur.execute("SELECT product_id,name,price_brl,stock_quantity,status,category_id FROM products WHERE product_id=%s", (product_id,))
            r = cur.fetchone()
        return None if not r else Product(r[0], r[1], Decimal(r[2]), r[3], r[4], r[5])
    def get_promotion(self, product_id):
        with self.conn.cursor() as cur:
            cur.execute("SELECT product_id,discount_percent,description,is_active FROM promotions WHERE product_id=%s AND is_active=TRUE LIMIT 1", (product_id,))
            r = cur.fetchone()
        return None if not r else Promotion(r[0], Decimal(r[1]), r[2], r[3])
    def get_order(self, order_id, verification=None):
        with self.conn.cursor() as cur:
            cur.execute("SELECT order_id,customer_id,status,total_brl FROM orders WHERE order_id=%s", (order_id,))
            r = cur.fetchone()
        if not r or verification != str(r[1]): return {"authorized": False, "reason": "verification_required"}
        return {"authorized": True, "order_id": r[0], "status": r[2], "total": Decimal(r[3])}
    def policy_search(self, query):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc: raise RuntimeError("Install policy retrieval support with: pip install -e '.[postgres]'") from exc
        vector = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")).encode(query, normalize_embeddings=True)
        vector_text = "[" + ",".join(str(float(x)) for x in vector) + "]"
        with self.conn.cursor() as cur:
            cur.execute("SELECT document_name,section,page,content FROM policy_chunks WHERE embedding IS NOT NULL ORDER BY embedding <=> %s::vector LIMIT 3", (vector_text,))
            return [{"document": r[0], "section": r[1], "page": r[2], "text": r[3]} for r in cur.fetchall()]

def reset_and_import(root: Path) -> dict:
    data = source_data_dir(root)
    files = {"categories": "categories", "products": "products", "promotions": "promotions", "customers": "customers", "orders": "orders", "order_items": "order_items"}
    with connect() as conn:
        conn.execute(SCHEMA.read_text(encoding="utf-8"))
        for table in ("order_items", "orders", "promotions", "products", "categories", "customers"): conn.execute(f"TRUNCATE {table} CASCADE")
        counts = {}
        for table, marker in files.items():
            path = next(p for p in data.glob("*.csv") if marker in p.stem.lower().replace(" ", "_"))
            values = rows(path)
            columns = list(values[0])
            with conn.cursor() as cur:
                cur.executemany(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join(['%s'] * len(columns))})", [tuple(r[c] for c in columns) for r in values])
            counts[table] = len(values)
        conn.commit()
    return counts

def policy_chunks(text: str, document: str, version: str = "2.1") -> list[dict]:
    chunks = []
    for page, page_text in enumerate(re.split(r"\f", text), 1):
        clean = " ".join(page_text.split())
        if not clean: continue
        section = next((line.strip(" :") for line in page_text.splitlines() if line.strip()), "unknown")[:120]
        digest = hashlib.sha256(f"{document}:{version}:{page}:{clean}".encode()).hexdigest()
        chunks.append({"document_name": document, "document_version": version, "section": section, "page": page, "content": clean, "source_hash": digest})
    return chunks

def ingest_policy(root: Path) -> int:
    try:
        from pypdf import PdfReader
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("Install policy ingestion support with: pip install -e '.[postgres]'") from exc
    data = source_data_dir(root)
    pdf = next(data.glob("*.pdf"), None)
    if pdf is None: raise FileNotFoundError("Policy PDF not found")
    pages = PdfReader(str(pdf)).pages
    text = "\f".join(page.extract_text() or "" for page in pages)
    chunks = policy_chunks(text, pdf.name)
    model = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
    vectors = model.encode([chunk["content"] for chunk in chunks], normalize_embeddings=True)
    if not vectors.size or vectors.shape[1] != 384: raise ValueError(f"Expected embedding dimension 384, got {vectors.shape[1]}")
    with connect() as conn:
        conn.execute(SCHEMA.read_text(encoding="utf-8"))
        with conn.cursor() as cur:
            for chunk, vector in zip(chunks, vectors):
                cur.execute("""INSERT INTO policy_chunks (document_name, document_version, section, page, content, embedding, source_hash)
                    VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (source_hash) DO UPDATE SET content=EXCLUDED.content, embedding=EXCLUDED.embedding""",
                    (*[chunk[k] for k in ("document_name", "document_version", "section", "page", "content")], "[" + ",".join(str(float(x)) for x in vector) + "]", chunk["source_hash"]))
        conn.commit()
    return len(chunks)
