"""Convert docs/rag_sources/ documents into normalized Gemini embeddings."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = REPO_ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.ai import EmbeddingError, embed_documents  # type: ignore  # noqa: E402
from rag_utils import chunk_text, iter_source_files, read_text  # noqa: E402

DEFAULT_SOURCE_DIR = REPO_ROOT / "docs" / "rag_sources"
DEFAULT_TARGET_PATH = REPO_ROOT / "docs" / "rag_vectors" / "corpus.parquet"


def build_records(files: List[Path]) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    for file_path in files:
        rel_path = file_path.relative_to(REPO_ROOT)
        text = read_text(file_path)
        chunks = chunk_text(text)
        for idx, chunk in enumerate(chunks):
            records.append(
                {
                    "doc_path": str(rel_path),
                    "chunk_index": idx,
                    "text": chunk,
                    "meta": {"source": str(rel_path)},
                }
            )
    return records


def embed_records(records: List[Dict[str, object]]) -> None:
    texts = [record["text"] for record in records]
    embeddings = embed_documents(texts)
    if len(embeddings) != len(records):
        raise RuntimeError("Mismatch between generated embeddings and records")
    for record, vector in zip(records, embeddings):
        record["embedding"] = vector.astype(float).tolist()


def save_vectors(records: List[Dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records, columns=["doc_path", "chunk_index", "text", "embedding", "meta"])
    df.to_parquet(output_path, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate RAG vectors from project documentation.")
    parser.add_argument("--source", type=str, default=str(DEFAULT_SOURCE_DIR), help="Directory containing source documents")
    parser.add_argument("--output", type=str, default=str(DEFAULT_TARGET_PATH), help="Parquet file path to write")
    args = parser.parse_args()

    source_dir = Path(args.source).resolve()
    output_path = Path(args.output).resolve()

    try:
        files = iter_source_files(source_dir)
        if not files:
            print("No source documents found; nothing to embed.")
            return 0
        records = build_records(files)
        embed_records(records)
        save_vectors(records, output_path)
        print(f"saved: {output_path} ({len(records)} chunks)")
        return 0
    except (EmbeddingError, FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
