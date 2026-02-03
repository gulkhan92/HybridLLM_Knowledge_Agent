# streamlit_app.py
import streamlit as st
from main import chunk_all_pdfs, build_faiss_from_ocr, build_graph, enrich_graph_with_entities, answer_query
from config import CHUNKING_METHODS

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="Hybrid Knowledge Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Custom CSS
# -----------------------------
st.markdown(
    """
    <style>
    /* General layout */
    body {
        background-color: #f4f6f8;
        color: #0f111b;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Sidebar */
    .css-1d391kg {  /* Streamlit sidebar class */
        background-color: #1f2937;
        color: #ffffff;
    }
    .css-1d391kg h2 {
        color: #ffffff;
    }

    /* Main header */
    .css-1d391kg + div h1 {
        font-size: 3rem;
        color: #111827;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #4f46e5;
        color: white;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-size: 1rem;
        font-weight: bold;
        transition: background 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #6366f1;
    }

    /* Text input */
    div.stTextInput > div > input {
        border-radius: 8px;
        padding: 0.5rem;
        font-size: 1rem;
    }

    /* Cards for answer & guardrail */
    .stMarkdown h2 {
        color: #4f46e5;
    }
    .card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("Settings")
chunk_method = st.sidebar.selectbox("Select Chunking Logic", CHUNKING_METHODS)
st.sidebar.markdown("---")
ingest_docs = st.sidebar.button("Run Full Ingestion Pipeline")

# -----------------------------
# Header
# -----------------------------
st.title("🤖 Hybrid Knowledge Agent")
st.markdown("Ask questions based on your PDF documents (supports scanned & handwritten text).")

# -----------------------------
# Ingestion
# -----------------------------
if ingest_docs:
    with st.spinner("🚀 Running ingestion pipeline... This may take a few minutes."):
        # 0️⃣ OCR is assumed done separately
        st.info("Chunking PDFs...")
        chunks = chunk_all_pdfs(method=chunk_method)
        st.success(f"✅ Total chunks prepared: {len(chunks)}")

        st.info("Building embeddings (FAISS)...")
        index, metadata = build_faiss_from_ocr()
        st.success(f"✅ FAISS index created with {len(metadata)} chunks")

        st.info("Ingesting chunks into Neo4j...")
        build_graph(chunks)
        st.success("✅ Neo4j graph populated")

        st.info("Extracting entities & enriching graph...")
        enrich_graph_with_entities()
        st.success("✅ Entities extracted and graph enriched")

        st.balloons()
        st.success("🎉 Ingestion pipeline completed successfully!")

from pdf_uploader import update_knowledge_base

# -----------------------------
# PDF Upload Section
# -----------------------------
st.markdown("## 📥 Upload a PDF to Update Knowledge Base")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file and st.button("Add PDF to Knowledge Base"):
    update_knowledge_base(uploaded_file, chunk_method=chunk_method)


# -----------------------------
# Query Section
# -----------------------------
st.markdown("## 💬 Ask a Question")
query = st.text_input("Enter your question here:")

if st.button("Get Answer") and query:
    with st.spinner("🧠 Generating answer..."):
        result = answer_query(query)
        
        # Display Answer
        st.markdown("### 📌 Answer")
        st.markdown(f'<div class="card">{result["answer"]}</div>', unsafe_allow_html=True)
        
        # Display Provenance
        st.markdown("### 🔍 Provenance (Chunks Used)")
        for c in result["chunks_used"]:
            st.markdown(
                f'<div class="card">{c["doc_id"]} | Page {c["page_number"]} | Chunk {c["chunk_id"]}</div>',
                unsafe_allow_html=True
            )
        
        # Display Guardrail
        st.markdown("### 🛡️ Guardrail Check")
        st.markdown(f'<div class="card">{result["guardrail"]}</div>', unsafe_allow_html=True)
