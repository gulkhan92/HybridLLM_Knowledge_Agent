# llm_query_and_guardrail.py
import json
from config import FAISS_INDEX_PATH, FAISS_METADATA_PATH, GROK_API_KEY, TOP_K
from embeddings import model, load_faiss_index
from neo4j import GraphDatabase
from groq import Groq
import numpy as np

# -----------------------------
# Initialize
# -----------------------------
client = Groq(api_key=GROK_API_KEY)

# Neo4j driver (optional)
driver = None
try:
    from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
except ImportError:
    print("Neo4j config not found. Only FAISS retrieval will work.")

# Load FAISS index and metadata
faiss_index, metadata = load_faiss_index(FAISS_INDEX_PATH)


# -----------------------------
# Retrieval Functions
# -----------------------------
def semantic_search(query, top_k=5):
    """Return top_k relevant chunks using FAISS."""
    q_vec = model.encode(query).reshape(1, -1)
    distances, indices = faiss_index.search(q_vec, top_k)
    results = [metadata[idx] for idx in indices[0] if idx < len(metadata)]
    return results


def graph_search_entities(query, top_k=5):
    """
    Retrieve chunk_ids from Neo4j that are linked to entities in the query.
    Simple entity matching; can be expanded for relationships or graph traversal.
    """
    if driver is None:
        return []

    # Extract keywords/entities from query (simple split for now)
    keywords = [w.lower() for w in query.split() if len(w) > 2]

    matched_chunks = []
    with driver.session() as session:
        for kw in keywords:
            result = session.run(
                """
                MATCH (e:Entity)-[:MENTIONS]-(c:Chunk)
                WHERE toLower(e.name) CONTAINS $kw
                RETURN c.chunk_id AS chunk_id, c.text AS text, c.page_number AS page_number, 
                       head([d IN [(c)<-[:HAS_CHUNK]-(doc:Document) | doc.doc_id] | d]) AS doc_id
                """,
                kw=kw
            )
            for record in result:
                matched_chunks.append({
                    "chunk_id": record["chunk_id"],
                    "text": record["text"],
                    "page_number": record["page_number"],
                    "doc_id": record["doc_id"]
                })

    # Remove duplicates
    unique_chunks = {c["chunk_id"]: c for c in matched_chunks}
    return list(unique_chunks.values())[:top_k]


def retrieve_chunks_for_context(query, top_k=TOP_K):
    """
    Hybrid retrieval: combine FAISS similarity + Neo4j entity matches.
    1. Get top chunks from FAISS.
    2. Get top chunks from KG.
    3. Merge and deduplicate (FAISS first, then KG if not included).
    """
    faiss_results = semantic_search(query, top_k)
    kg_results = graph_search_entities(query, top_k)

    # Deduplicate KG results not already in FAISS
    faiss_ids = {c["chunk_id"] for c in faiss_results}
    hybrid_results = faiss_results + [c for c in kg_results if c["chunk_id"] not in faiss_ids]

    # Limit total results to top_k
    return hybrid_results[:top_k]


# -----------------------------
# LLM Calls
# -----------------------------
def call_llm(messages, temperature=1, max_tokens=1024):
    """Call Groq LLM with streaming response."""
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_tokens,
        top_p=1,
        stream=True,
        stop=None
    )

    # Collect streamed response
    full_response = ""
    for chunk in completion:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="", flush=True)
            full_response += content
    print()
    return full_response


def generate_answer(query, context_chunks):
    """Generate answer using LLM."""
    context_text = "\n\n".join(
        [f"Document: {c['doc_id']}, Page: {c['page_number']}, Chunk: {c['chunk_id']}\nText: {c['text']}" for c in context_chunks]
    )

    messages = [
        {"role": "system", "content": "You are a helpful assistant answering based on internal knowledge."},
        {"role": "user", "content": f"Answer the following question using the context below:\n\n{context_text}\n\nQuestion: {query}"}
    ]

    return call_llm(messages)


def guardrail_check(answer, context_chunks, query):
    """Validate the answer using a second LLM call."""
    context_text = "\n\n".join(
        [f"Document: {c['doc_id']}, Page: {c['page_number']}, Chunk: {c['chunk_id']}\nText: {c['text']}" for c in context_chunks]
    )

    messages = [
        {"role": "system", "content": "You are an AI guardrail checking for accuracy and hallucinations and respond with very concise logic."},
        {"role": "user", "content": f"Validate the following answer based on context:\n\n{context_text}\n\nAnswer: {answer}\n\nQuestion: {query}\n\nDoes this answer only use internal knowledge and cite sources correctly? Provide the final verdict: Passed, Failed, or Partially Passed."}
    ]

    return call_llm(messages)


# -----------------------------
# Main Query Function
# -----------------------------
def answer_query(query, top_k=TOP_K):
    """Full pipeline: hybrid retrieval -> LLM answer -> guardrail."""
    context_chunks = retrieve_chunks_for_context(query, top_k)
    if not context_chunks:
        return "No relevant context found in knowledge base."

    print("\nAnswer:")
    answer = generate_answer(query, context_chunks)

    print("\nGuardrail check:")
    guardrail_result = guardrail_check(answer, context_chunks, query)

    return {
        "answer": answer,
        "guardrail": guardrail_result,
        "chunks_used": context_chunks
    }


if __name__ == "__main__":
    q = input("Enter your question: ")
    result = answer_query(q)
    print("\nFinal Answer:", result["answer"])
    print("\nGuardrail Result:", result["guardrail"])
    print("\nChunks Used:")
    for c in result["chunks_used"]:
        print(f"{c['doc_id']} - Page {c['page_number']} - Chunk {c['chunk_id']}")


# # llm_query_and_guardrail.py
# import json
# from config import FAISS_INDEX_PATH, FAISS_METADATA_PATH, GROK_API_KEY
# from embeddings import model, load_faiss_index
# from neo4j import GraphDatabase
# from groq import Groq
# import numpy as np
# from config import (
#     VECTOR_DIM,
#     EMBEDDING_MODEL_NAME,
#     FAISS_INDEX_PATH,
#     FAISS_METADATA_PATH,
#     NEO4J_URI,
#     NEO4J_USER,
#     NEO4J_PASSWORD,
#     GROK_API_KEY,
#     TOP_K
# )
# # -----------------------------
# # Initialize
# # -----------------------------
# client = Groq(api_key=GROK_API_KEY)  # Changed: Added api_key parameter
# driver = None
# try:
#     from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
#     driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
# except ImportError:
#     print("Neo4j config not found. Only FAISS retrieval will work.")

# # Load FAISS index and metadata
# # faiss_index = load_faiss_index(FAISS_INDEX_PATH)
# # with open(FAISS_METADATA_PATH, "r", encoding="utf-8") as f:
# #     metadata = json.load(f)

# faiss_index, metadata = load_faiss_index(FAISS_INDEX_PATH)


# # -----------------------------
# # Retrieval Functions
# # -----------------------------
# def semantic_search(query, top_k=5):
#     """Return top_k relevant chunks using FAISS."""
#     q_vec = model.encode(query).reshape(1, -1)
#     distances, indices = faiss_index.search(q_vec, top_k)
#     results = [metadata[idx] for idx in indices[0] if idx < len(metadata)]
#     return results

# def retrieve_chunks_for_context(query, top_k=5):
#     """Retrieve chunks from Neo4j and FAISS for a query."""
#     faiss_results = semantic_search(query, top_k)
#     # Optional: filter using Neo4j if needed for structured context
#     return faiss_results

# # -----------------------------
# # LLM Calls
# # -----------------------------
# def call_llm(messages, temperature=1, max_tokens=1024):
#     """Call Groq LLM with streaming response."""
#     completion = client.chat.completions.create(
#         model="meta-llama/llama-4-scout-17b-16e-instruct",
#         messages=messages,
#         temperature=temperature,
#         max_completion_tokens=max_tokens,
#         top_p=1,
#         stream=True,
#         stop=None
#     )

#     # Collect streamed response
#     full_response = ""
#     for chunk in completion:
#         content = chunk.choices[0].delta.content
#         if content:
#             print(content, end="", flush=True)
#             full_response += content
#     print()  # New line after stream
#     return full_response

# def generate_answer(query, context_chunks):
#     """Generate answer using LLM."""
#     context_text = "\n\n".join(
#         [f"Document: {c['doc_id']}, Page: {c['page_number']}, Chunk: {c['chunk_id']}\nText: {c['text']}" for c in context_chunks]
#     )

#     messages = [
#         {"role": "system", "content": "You are a helpful assistant answering based on internal knowledge."},
#         {"role": "user", "content": f"Answer the following question using the context below:\n\n{context_text}\n\nQuestion: {query}"}
#     ]

#     answer = call_llm(messages)
#     return answer

# def guardrail_check(answer, context_chunks, query):
#     """Validate the answer using a second LLM call."""
#     context_text = "\n\n".join(
#         [f"Document: {c['doc_id']}, Page: {c['page_number']}, Chunk: {c['chunk_id']}\nText: {c['text']}" for c in context_chunks]
#     )

#     messages = [
#         {"role": "system", "content": "You are an AI guardrail checking for accuracy and hallucinations and respond with very concise logic."},
#         {"role": "user", "content": f"Validate the following answer based on context:\n\n{context_text}\n\nAnswer: {answer}\n\nQuestion: {query}\n\nDoes this answer only use internal knowledge and cite sources correctly? \n Provide the final verdict as well, i.e., Passed, Failed or Partially Passed."}
#     ]

#     result = call_llm(messages)
#     return result

# # -----------------------------
# # Main Query Function
# # -----------------------------
# def answer_query(query, top_k=5):
#     """Full pipeline: retrieve, answer, guardrail."""
#     context_chunks = retrieve_chunks_for_context(query, top_k)
#     if not context_chunks:
#         return "No relevant context found in knowledge base."

#     print("\nAnswer:")
#     answer = generate_answer(query, context_chunks)

#     print("\nGuardrail check:")
#     guardrail_result = guardrail_check(answer, context_chunks, query)

#     return {
#         "answer": answer,
#         "guardrail": guardrail_result,
#         "chunks_used": context_chunks
#     }

# # 
# if __name__ == "__main__":
#     q = input("Enter your question: ")
#     result = answer_query(q)
#     print("\nFinal Answer:", result["answer"])
#     print("\nGuardrail Result:", result["guardrail"])
#     print("\nChunks Used:")
#     for c in result["chunks_used"]:
#         print(f"{c['doc_id']} - Page {c['page_number']} - Chunk {c['chunk_id']}")
