# embeddings.py
import os
import json
import faiss
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from config import (
    VECTOR_DIM,
    EMBEDDING_MODEL_NAME,
    FAISS_INDEX_PATH,
    FAISS_METADATA_PATH
)
# from config import (
#     VECTOR_DIM,
#     EMBEDDING_MODEL_NAME,
#     FAISS_INDEX_PATH,
#     FAISS_METADATA_PATH,
#     FAISS_INDEX_FILE,       
#     FAISS_METADATA_FILE     
# )

from chunking import chunk_all_pdfs

# -----------------------------
# Initialize Model
# -----------------------------
model = SentenceTransformer(EMBEDDING_MODEL_NAME)
# faiss.write_index(index, FAISS_INDEX_PATH)

# -----------------------------
# FAISS Functions
# -----------------------------
def create_faiss_index(chunks, model=model, vector_dim=VECTOR_DIM):
    """
    Create a FAISS index from a list of chunk dictionaries.
    Each chunk must contain 'text', 'doc_id', 'chunk_id', 'page_number'.
    Returns the FAISS index and metadata list.
    """
    index = faiss.IndexFlatL2(vector_dim)
    metadata = []

    for chunk in tqdm(chunks, desc="Creating embeddings"):
        embedding = model.encode(chunk["text"]).reshape(1, -1)
        index.add(embedding)
        metadata.append(chunk)

    return index, metadata

def save_faiss_index(index, metadata, index_file=FAISS_INDEX_PATH, metadata_file=FAISS_METADATA_PATH):
    """
    Save FAISS index and metadata to disk.
    """
    faiss.write_index(index, index_file)
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"FAISS index saved to {index_file}")
    print(f"Metadata saved to {metadata_file}")

def load_faiss_index(index_file=FAISS_INDEX_PATH, metadata_file=FAISS_METADATA_PATH):
    """
    Load FAISS index and metadata from disk.
    Returns index and metadata list.
    """
    if not os.path.exists(index_file) or not os.path.exists(metadata_file):
        raise FileNotFoundError("FAISS index or metadata file not found.")

    index = faiss.read_index(index_file)
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print(f"FAISS index loaded from {index_file}")
    print(f"Metadata loaded from {metadata_file}")
    return index, metadata

def search_faiss(query, index, metadata, top_k=5, model=model):
    """
    Search FAISS index for similar chunks.
    Returns top_k matching chunk dictionaries.
    """
    query_embedding = model.encode(query).reshape(1, -1)
    distances, indices = index.search(query_embedding, top_k)

    results = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx < len(metadata):
            results.append({
                "chunk": metadata[idx],
                "score": float(dist)
            })
    return results

# -----------------------------
# Wrapper for full ingestion
# -----------------------------
def build_faiss_from_ocr():
    """
    Build FAISS index from chunks obtained via chunking.py
    Returns index and metadata.
    """
    chunks = chunk_all_pdfs()
    print(f"Loaded {len(chunks)} chunks from chunking module")
    index, metadata = create_faiss_index(chunks)
    save_faiss_index(index, metadata)
    return index, metadata
