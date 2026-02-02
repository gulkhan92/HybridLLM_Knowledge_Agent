# graph.py
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from chunking import chunk_all_pdfs

# -----------------------------
# Neo4j Initialization
# -----------------------------
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# -----------------------------
# Graph Helper Functions
# -----------------------------
def clear_neo4j(tx):
    """Delete all nodes and relationships in Neo4j."""
    tx.run("MATCH (n) DETACH DELETE n")

def create_document_node(tx, doc_id, title):
    """Create or merge a document node."""
    tx.run(
        """
        MERGE (d:Document {doc_id: $doc_id})
        SET d.title = $title
        """,
        doc_id=doc_id,
        title=title
    )

def create_chunk_node(tx, chunk):
    """Create a chunk node and link it to the corresponding document."""
    tx.run(
        """
        MERGE (c:Chunk {chunk_id: $chunk_id})
        SET c.text = $text, c.page_number = $page_number
        WITH c
        MATCH (d:Document {doc_id: $doc_id})
        MERGE (d)-[:HAS_CHUNK]->(c)
        """,
        chunk_id=chunk["chunk_id"],
        text=chunk["text"],
        page_number=chunk["page_number"],
        doc_id=chunk["doc_id"]
    )

def get_all_chunks():
    """
    Fetch all chunks from OCR storage or chunking module.
    Returns a list of chunks with fields: doc_id, page_number, chunk_id, text.
    """
    # Assuming chunk_all_pdfs returns a list of dicts with proper fields
    return chunk_all_pdfs(method="default")

# -----------------------------
# Graph Population / Hybrid Ready
# -----------------------------
def build_graph(chunks=None, clear_existing=True):
    """
    Populate Neo4j with Documents and Chunks.
    Supports hybrid search by enabling entity linking later.
    If chunks is None, fetch all chunks using chunking module.
    """
    if chunks is None:
        chunks = get_all_chunks()

    total_docs = len(set(c["doc_id"] for c in chunks))
    total_chunks = len(chunks)

    with driver.session() as session:
        if clear_existing:
            print("Clearing existing Neo4j graph...")
            session.execute_write(clear_neo4j)

        # Create Document nodes
        doc_ids = set(chunk["doc_id"] for chunk in chunks)
        for doc_id in doc_ids:
            session.execute_write(create_document_node, doc_id, doc_id)

        # Create Chunk nodes
        for idx, chunk in enumerate(chunks, 1):
            session.execute_write(create_chunk_node, chunk)
            if idx % 50 == 0:
                print(f"Created {idx}/{total_chunks} chunks...")

    print(f"Neo4j graph built: {total_docs} documents, {total_chunks} chunks")


# # graph.py
# from neo4j import GraphDatabase
# from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
# from chunking import chunk_all_pdfs

# # -----------------------------
# # Neo4j Initialization
# # -----------------------------
# driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# # -----------------------------
# # Graph Helper Functions
# # -----------------------------

# def clear_neo4j(tx):
#     """Delete all nodes and relationships in Neo4j."""
#     tx.run("MATCH (n) DETACH DELETE n")

# def create_document_node(tx, doc_id, title):
#     """Create or merge a document node."""
#     tx.run(
#         "MERGE (d:Document {doc_id: $doc_id}) "
#         "SET d.title = $title",
#         doc_id=doc_id,
#         title=title
#     )

# def create_chunk_node(tx, chunk):
#     """Create a chunk node and link it to the document."""
#     tx.run(
#         "MERGE (c:Chunk {chunk_id: $chunk_id}) "
#         "SET c.text = $text, c.page_number = $page_number "
#         "WITH c "
#         "MATCH (d:Document {doc_id: $doc_id}) "
#         "MERGE (d)-[:HAS_CHUNK]->(c)",
#         chunk_id=chunk["chunk_id"],
#         text=chunk["text"],
#         page_number=chunk["page_number"],
#         doc_id=chunk["doc_id"]
#     )

# # -----------------------------
# # Graph Population
# # -----------------------------
# def build_graph(chunks=None, clear_existing=True):
#     """
#     Populate Neo4j with Documents and Chunks.
#     If chunks is None, fetch from chunking module.
#     """
#     if chunks is None:
#         chunks = get_all_chunks()

#     with driver.session() as session:
#         if clear_existing:
#             print("Clearing existing Neo4j graph...")
#             session.execute_write(clear_neo4j)

#         # Create Document nodes
#         doc_ids = set(chunk["doc_id"] for chunk in chunks)
#         for doc_id in doc_ids:
#             session.execute_write(create_document_node, doc_id, doc_id)

#         # Create Chunk nodes
#         for chunk in chunks:
#             session.execute_write(create_chunk_node, chunk)

#     print(f"Neo4j graph built: {len(doc_ids)} documents, {len(chunks)} chunks")
