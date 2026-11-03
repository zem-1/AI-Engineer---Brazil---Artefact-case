from __future__ import annotations

import csv, hashlib, os, re
from pathlib import Path

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
