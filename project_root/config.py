# config.py
import os

# -----------------------------
# Neo4j Config
# -----------------------------
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Neo4j123!"

# -----------------------------
# FAISS / Embeddings Config
# -----------------------------
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # lightweight model
VECTOR_DIM = 384                           # embedding dimension
FAISS_INDEX_PATH = "/Users/dev/Downloads/ADEO AI Assessment/HybridLLM_Knowledge_Agent/faiss_index.idx"
FAISS_METADATA_PATH = "/Users/dev/Downloads/ADEO AI Assessment/HybridLLM_Knowledge_Agent/faiss_metadata.json"
# -----------------------------
# OCR / PDF Config
# -----------------------------
OCR_CHUNKS_FOLDER = "/Users/dev/Downloads/ADEO AI Assessment/HybridLLM_Knowledge_Agent/ocr_chunks"
SUPPORTED_EXTENSIONS = [".pdf"]

# -----------------------------
# Chunking Options
# -----------------------------
CHUNKING_METHODS = [
    "sentence",      # sentence-wise chunking
    "paragraph",     # paragraph-wise chunking
    "fixed_length"   # fixed-length character chunks
]

# -----------------------------
# General Settings
# -----------------------------
LOGGING_ENABLED = True

# LLM Configs 
GROK_API_KEY="GROQ_API_KEY"

# Top K chunks retrieval
TOP_K =5