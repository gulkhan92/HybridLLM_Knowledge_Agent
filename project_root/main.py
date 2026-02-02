# main.py
import argparse
from ocr import ocr_multiple_pdfs
from chunking import chunk_all_pdfs
from embeddings import build_faiss_from_ocr
from graph import build_graph
from entities import enrich_graph_with_entities
from llm_query_and_guardrail import answer_query
from config import OCR_CHUNKS_FOLDER, SUPPORTED_EXTENSIONS
from pathlib import Path

def main(args):
    # -----------------------------
    # INGESTION PIPELINE
    # -----------------------------
    if args.ingest:
        print("\n🚀 Starting document ingestion pipeline...\n")

        # 0️⃣ Collect PDF files
        pdf_paths = [str(p) for p in Path(args.pdf_folder).glob("*") if p.suffix.lower() in SUPPORTED_EXTENSIONS]
        if not pdf_paths:
            print("❌ No PDF files found in folder:", args.pdf_folder)
            return

        print("0️⃣ Performing OCR on PDFs")
        ocr_multiple_pdfs(pdf_paths)

        print("\n1️⃣ Chunking PDFs")
        chunks = chunk_all_pdfs()
        print(f"✅ Total chunks prepared: {len(chunks)}")

        print("\n2️⃣ Building embeddings (FAISS)")
        index, metadata = build_faiss_from_ocr()
        print(f"✅ FAISS index created with {len(metadata)} chunks")

        print("\n3️⃣ Ingesting chunks into Neo4j")
        build_graph(chunks)
        print("✅ Neo4j graph populated")

        print("\n4️⃣ Extracting entities & enriching graph")
        enrich_graph_with_entities()
        print("✅ Entities extracted and graph enriched")

        print("\n🎉 Ingestion pipeline completed successfully.\n")

    # -----------------------------
    # QUERY LOOP
    # -----------------------------
    print("💬 Hybrid Knowledge Agent is ready to answer questions.")
    while True:
        query = input("\nAsk a question (or type 'exit'): ")
        if query.lower() == "exit":
            break

        result = answer_query(query)

        print("\n📌 FINAL ANSWER")
        print(result["answer"])

        print("\n🔍 PROVENANCE")
        for c in result["chunks_used"]:
            print(f"- {c['doc_id']} | Page {c['page_number']} | Chunk {c['chunk_id']}")

        print("\n🛡️ GUARDRAIL")
        print(result["guardrail"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hybrid LLM Knowledge Agent")
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Run full ingestion pipeline (OCR → chunking → embeddings → graph → entities)"
    )
    parser.add_argument(
        "--pdf_folder",
        type=str,
        default="pdfs",
        help="Folder containing PDFs to ingest"
    )

    args = parser.parse_args()
    main(args)
