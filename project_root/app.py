# streamlit_app.py
import streamlit as st
from main import chunk_all_pdfs, build_faiss_from_ocr, build_graph, enrich_graph_with_entities, answer_query
from config import CHUNKING_METHODS
from pdf_uploader import update_knowledge_base

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
# CUSTOM CSS
# -----------------------------
st.markdown("""
<style>
    /* Import Inter Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* GLOBAL RESET */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1f2937;
    }

    /* BACKGROUND */
    .stApp {
        background-color: #f4f6f9;
    }

    /* -------------------
       SIDEBAR STYLING 
       ------------------- */
    section[data-testid="stSidebar"] {
        background-color: #1e293b; /* Navy Slate */
        color: #f1f5f9;
    }
    
    /* General Sidebar Text */
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: #f1f5f9 !important;
    }

    /* FORCE BLACK BOLD TEXT IN SIDEBAR INPUTS */
    /* Selectbox (Dropdown) */
    [data-testid="stSidebar"] [data-baseweb="select"] div {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: 700 !important;
    }
    /* Dropdown text when opening */
    div[data-baseweb="popover"] div {
        color: #000000 !important;
        font-weight: 600 !important;
    }

    /* File Uploader */
    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 10px;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] section {
        background-color: #ffffff;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] div,
    [data-testid="stSidebar"] [data-testid="stFileUploader"] small, 
    [data-testid="stSidebar"] [data-testid="stFileUploader"] span {
        color: #000000 !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button {
        color: #000000 !important; 
        border-color: #000000 !important;
    }

    /* -------------------
       MAIN CONTENT 
       ------------------- */
    
    /* Content Card */
    .content-box {
        background: #ffffff;
        padding: 2rem;
        margin-top: 1rem;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
    }

    /* Result Typography */
    .answer-text {
        font-size: 1.1rem;
        line-height: 1.6;
        color: #1f2937;
        margin-bottom: 20px;
    }

    /* Guardrail Badge */
    .guardrail-box {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #166534;
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-block;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    /* Source Cards */
    .source-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-top: 10px;
    }
    .source-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        font-size: 0.85rem;
    }

    /* Inputs & Buttons */
    div.stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        padding: 12px;
        font-size: 1rem;
        color: #374151;
        background-color: #ffffff;
    }
    div.stButton > button {
        background-color: #2563eb;
        color: white;
        border: none;
        padding: 0.75rem 1.4rem;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
        transition: 0.2s;
    }
    div.stButton > button:hover {
        background-color: #1e4ed8;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("# ⚙️ Control Panel")
    
    # 1. Chunking
    st.markdown("### Configurations")
    chunk_method = st.selectbox("Chunking Strategy", CHUNKING_METHODS)

    st.write("") 

    # 2. Ingestion Button
    if st.button("🚀 Run Full Ingestion Pipeline"):
        st.markdown("---")
        with st.spinner("Running pipeline..."):
            st.text("Processing Documents...")
            chunks = chunk_all_pdfs(method=chunk_method)
            st.text(f"✅ Chunks: {len(chunks)}")

            st.text("Updating Vector Index...")
            index, metadata = build_faiss_from_ocr()
            
            st.text("Building Graph...")
            build_graph(chunks)
            enrich_graph_with_entities()
            
            st.success("Ingestion pipeline completed!")
    
    # Description below button
    st.caption("Re-processes all PDFs and update the Graph & Vector stores.")

    st.markdown("---")

    # 3. Upload Section
    st.markdown("### Add Document to Update Knowledge Base")
    # st.markdown("### Update Knowledge Base")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    if uploaded_file and st.button("Update Knowledge Base"):
        with st.spinner("Uploading & Indexing..."):
            update_knowledge_base(uploaded_file, chunk_method=chunk_method)
            st.success("✅ PDF added successfully!")

# -----------------------------
# Main Page
# -----------------------------

# Header
col_av, col_txt = st.columns([1, 8])
with col_av:
    st.markdown('<div style="font-size:3rem; text-align:center;">🤖</div>', unsafe_allow_html=True)
with col_txt:
    st.markdown("# Hybrid LLM Knowledge Agent")
    st.markdown("<p style='color: #64748b;'>Intelligent Document Analysis with Automated Hybrid Retrieval - Neo4j(Knowledge Graph) & FAISS(Vector Search)</p>", unsafe_allow_html=True)

# Main Content Card
st.markdown('<div class="content-box">', unsafe_allow_html=True)
st.markdown("### Ask a Question")

# Input & Button
c1, c2 = st.columns([5, 1])
with c1:
    query = st.text_input("Question", placeholder="Type your question here...", label_visibility="collapsed")
with c2:
    st.markdown('<div style="margin-top: 2px;"></div>', unsafe_allow_html=True) 
    submit_btn = st.button("Analyze")

st.markdown('</div>', unsafe_allow_html=True) # Close Input Card


# Logic: Generate and Show Answer
if submit_btn and query:
    with st.spinner("Analyzing Knowledge Graph..."):
        result = answer_query(query)

        # We create a single HTML block for the answer to ensure correct rendering order
        # Structure: Answer -> Guardrail -> Sources
        
        # 1. Answer & Guardrail HTML

        # ... (rest of the file above) ...

# -----------------------------
# LOGIC: Generate and Show Answer
# -----------------------------
if submit_btn and query:
    with st.spinner("Analyzing Knowledge Graph..."):
        result = answer_query(query)
        
        # Format text to handle newlines in HTML
        formatted_answer = result["answer"].replace("\n", "<br>")
        formatted_guardrail = result["guardrail"].replace("\n", "<br>")

        # ---------------------------------------------------------
        # ROBUST HTML GENERATION (Indentation-Safe)
        # Using string concatenation ensures no spaces break the HTML
        # ---------------------------------------------------------
        answer_html = (
            '<div class="content-box">'
                '<h3 style="margin-bottom: 15px; color: #111827; font-weight: 700;">Analysis Result</h3>'
                
                # Answer Text
                f'<div style="font-size: 1.05rem; line-height: 1.7; color: #374151; margin-bottom: 25px;">'
                    f'{formatted_answer}'
                '</div>'
                
                '<hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0;">'

                # Guardrail Box
                '<div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px 16px; border-radius: 8px;">'
                    '<strong style="color: #15803d; display: block; margin-bottom: 4px; font-size: 0.9rem;">'
                        '🛡️ Guardrail Check'
                    '</strong>'
                    f'<div style="color: #166534; font-size: 0.9rem; line-height: 1.5;">'
                        f'{formatted_guardrail}'
                    '</div>'
                '</div>'
            '</div>'
        )
        
        # Render the Main Answer Card
        st.markdown(answer_html, unsafe_allow_html=True)

        # ---------------------------------------------------------
        # Source Provenance (Grid Layout)
        # ---------------------------------------------------------
        st.markdown("### 🔍 Source Provenance")
        
        if result["chunks_used"]:
            chunks = result["chunks_used"]
            # Create columns for grid effect (3 per row)
            cols = st.columns(3)
            for i, c in enumerate(chunks):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="content-box" style="padding: 15px; margin-top: 10px; min-height: 100px;">
                        <div style="font-weight: 700; color: #1f2937; margin-bottom: 5px;">
                            📄 {c['doc_id']}
                        </div>
                        <div style="font-size: 0.85rem; color: #6b7280;">
                            Page {c['page_number']} <br> Chunk {c['chunk_id']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


        # # 2. Source Provenance (Rendered separately for Grid layout)
        # st.markdown("### 🔍 Source Provenance")
        
        # if result["chunks_used"]:
        #     chunks = result["chunks_used"]
        #     # Create columns for grid effect
        #     cols = st.columns(3)
        #     for i, c in enumerate(chunks):
        #         with cols[i % 3]:
        #             st.markdown(f"""
        #             <div class="content-box" style="padding: 15px; margin-top: 0; min-height: 100px;">
        #                 <div style="font-weight: 700; color: #1f2937; margin-bottom: 5px;">
        #                     📄 {c['doc_id']}
        #                 </div>
        #                 <div style="font-size: 0.85rem; color: #6b7280;">
        #                     Page {c['page_number']} <br> Chunk {c['chunk_id']}
        #                 </div>
        #             </div>
        #             """, unsafe_allow_html=True)