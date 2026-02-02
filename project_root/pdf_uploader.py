# pdf_uploader.py
import os
from pathlib import Path
import shutil
import streamlit as st
from ocr import ocr_pdf
from chunking import chunk_all_pdfs
from embeddings import build_faiss_from_ocr
from graph import build_graph
from entities import enrich_graph_with_entities

UPLOAD_FOLDER = "uploaded_pdfs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_uploaded_pdf(uploaded_file):
    """Save the uploaded PDF to the upload folder."""
    pdf_path = Path(UPLOAD_FOLDER) / uploaded_file.name
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return pdf_path

def update_knowledge_base(uploaded_file, chunk_method="sentence"):
    """
    Process a new PDF:
    1. Save PDF
    2. Run OCR
    3. Chunk text
    4. Update FAISS index
    5. Update Neo4j graph
    6. Enrich graph with entities
    """
    st.info(f"Saving uploaded file: {uploaded_file.name}")
    pdf_path = save_uploaded_pdf(uploaded_file)

    st.info("Performing OCR...")
    ocr_pdf(pdf_path)

    st.info("Chunking PDF...")
    chunks = chunk_all_pdfs(method=chunk_method)
    st.success(f"✅ Total chunks prepared: {len(chunks)}")

    st.info("Building/Updating embeddings (FAISS)...")
    build_faiss_from_ocr()
    st.success("✅ FAISS index updated")

    st.info("Updating Neo4j graph...")
    build_graph(chunks)
    st.success("✅ Graph updated with new chunks")

    st.info("Extracting entities and enriching graph...")
    enrich_graph_with_entities()
    st.success("✅ Entities extracted and graph enriched")

    st.balloons()
    st.success(f"Knowledge base updated successfully with {uploaded_file.name}")
