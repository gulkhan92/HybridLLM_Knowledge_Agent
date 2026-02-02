# chunking.py
import os
from pathlib import Path
import re
from typing import List, Dict
from nltk import sent_tokenize
from config import OCR_CHUNKS_FOLDER, CHUNKING_METHODS

# -----------------------------
# Helper Functions
# -----------------------------

def read_text_file(file_path: str) -> str:
    """Read text from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def sentence_chunking(text: str) -> List[str]:
    """Split text into sentences using nltk."""
    return sent_tokenize(text)

def paragraph_chunking(text: str) -> List[str]:
    """Split text into paragraphs based on double newline."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs

def fixed_length_chunking(text: str, chunk_size: int = 500) -> List[str]:
    """
    Split text into fixed-length chunks (by characters).
    Default chunk_size=500 chars.
    """
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def chunk_text(text: str, method: str = "sentence", chunk_size: int = 500) -> List[str]:
    """
    Chunk text based on selected method.
    method: sentence | paragraph | fixed_length
    """
    if method == "sentence":
        return sentence_chunking(text)
    elif method == "paragraph":
        return paragraph_chunking(text)
    elif method == "fixed_length":
        return fixed_length_chunking(text, chunk_size)
    else:
        raise ValueError(f"Unknown chunking method: {method}")

# -----------------------------
# Main Chunking Function
# -----------------------------

def chunk_pdf_texts(pdf_folder: str, method: str = "sentence", chunk_size: int = 500) -> List[Dict]:
    """
    Read all OCR text files for a PDF and return chunk dictionaries.
    Returns a list of dicts with keys: doc_id, chunk_id, page_number, text
    """
    pdf_name = Path(pdf_folder).name
    chunks_list = []

    text_files = sorted([f for f in os.listdir(pdf_folder) if f.endswith(".txt")])
    
    for txt_file in text_files:
        text_path = Path(pdf_folder) / txt_file
        text = read_text_file(text_path)

        # Chunking
        sub_chunks = chunk_text(text, method=method, chunk_size=chunk_size)

        for i, chunk_text_content in enumerate(sub_chunks):
            chunk_dict = {
                "doc_id": pdf_name,
                "chunk_id": f"{txt_file.split('.txt')[0]}_{i+1}",
                "page_number": int(re.search(r"_p(\d+)_", txt_file).group(1)),
                "text": chunk_text_content
            }
            chunks_list.append(chunk_dict)

    return chunks_list

def chunk_all_pdfs(ocr_base_folder: str = OCR_CHUNKS_FOLDER,
                   method: str = "sentence",
                   chunk_size: int = 500) -> List[Dict]:
    """
    Chunk all PDFs inside OCR_CHUNKS_FOLDER
    """
    pdf_folders = [f for f in os.listdir(ocr_base_folder) if os.path.isdir(os.path.join(ocr_base_folder, f))]
    all_chunks = []

    for pdf_name in pdf_folders:
        pdf_dir = os.path.join(ocr_base_folder, pdf_name)
        pdf_chunks = chunk_pdf_texts(pdf_dir, method=method, chunk_size=chunk_size)
        all_chunks.extend(pdf_chunks)

    return all_chunks
