# entities.py
import spacy
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# -----------------------------
# Load NLP Model
# -----------------------------
nlp = spacy.load("en_core_web_sm")  # Swap with larger model if needed

# -----------------------------
# Neo4j Initialization
# -----------------------------
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# -----------------------------
# Entity Extraction Functions
# -----------------------------
def extract_entities(text):
    """
    Extract named entities from text using SpaCy.
    Returns a list of dicts: [{"text": entity_text, "label": entity_label}, ...]
    """
    doc = nlp(text)
    return [{"text": ent.text, "label": ent.label_} for ent in doc.ents]

def create_entity_node(tx, entity_text, entity_label):
    """Create or merge an Entity node in Neo4j."""
    tx.run(
        """
        MERGE (e:Entity {name: $entity_text})
        SET e.label = $entity_label
        """,
        entity_text=entity_text,
        entity_label=entity_label
    )

def link_chunk_to_entity(tx, chunk_id, entity_text):
    """Link a Chunk node to an Entity node in Neo4j."""
    tx.run(
        """
        MATCH (c:Chunk {chunk_id: $chunk_id}), (e:Entity {name: $entity_text})
        MERGE (c)-[:MENTIONS]->(e)
        """,
        chunk_id=chunk_id,
        entity_text=entity_text
    )

# -----------------------------
# Graph Enrichment
# -----------------------------
def enrich_graph_with_entities(chunks=None):
    """
    Extract entities from chunks and populate the Neo4j graph.
    If chunks is None, fetch all chunks from Neo4j.
    """
    with driver.session() as session:
        # If chunks not provided, fetch all chunks from Neo4j
        if chunks is None:
            chunks = []
            result = session.run("MATCH (c:Chunk) RETURN c.chunk_id AS chunk_id, c.text AS text")
            for record in result:
                chunks.append({"chunk_id": record["chunk_id"], "text": record["text"]})

        total_chunks = len(chunks)
        print(f"Starting entity extraction for {total_chunks} chunks...")

        for idx, chunk in enumerate(chunks, 1):
            entities = extract_entities(chunk["text"])
            for ent in entities:
                session.execute_write(create_entity_node, ent["text"], ent["label"])
                session.execute_write(link_chunk_to_entity, chunk["chunk_id"], ent["text"])
            if idx % 50 == 0:
                print(f"Processed {idx}/{total_chunks} chunks...")

    print(f"Entity extraction and graph enrichment complete! Total chunks processed: {total_chunks}")

# # entities.py
# import spacy
# from neo4j import GraphDatabase
# from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# # -----------------------------
# # Load NLP Model
# # -----------------------------
# nlp = spacy.load("en_core_web_sm")  # Can be swapped with larger model if needed

# # -----------------------------
# # Neo4j Initialization
# # -----------------------------
# driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# # -----------------------------
# # Entity Extraction Functions
# # -----------------------------
# def extract_entities(text):
#     """Return list of entities with their label and text."""
#     doc = nlp(text)
#     entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
#     return entities

# def create_entity_node(tx, entity_text, entity_label):
#     """Create or merge entity node."""
#     tx.run(
#         "MERGE (e:Entity {name: $entity_text}) "
#         "SET e.label = $entity_label",
#         entity_text=entity_text,
#         entity_label=entity_label
#     )

# def link_chunk_entity(tx, chunk_id, entity_text):
#     """Link a chunk to an entity."""
#     tx.run(
#         "MATCH (c:Chunk {chunk_id: $chunk_id}), (e:Entity {name: $entity_text}) "
#         "MERGE (c)-[:MENTIONS]->(e)",
#         chunk_id=chunk_id,
#         entity_text=entity_text
#     )

# # -----------------------------
# # Full Graph Enrichment
# # -----------------------------
# def enrich_graph_with_entities(chunks=None):
#     """
#     Extract entities from chunks and populate Neo4j.
#     If chunks is None, fetch all chunks from Neo4j.
#     """
#     with driver.session() as session:
#         if chunks is None:
#             chunks = []
#             result = session.run("MATCH (c:Chunk) RETURN c.chunk_id AS chunk_id, c.text AS text")
#             for record in result:
#                 chunks.append({"chunk_id": record["chunk_id"], "text": record["text"]})

#         for chunk in chunks:
#             entities = extract_entities(chunk["text"])
#             for ent in entities:
#                 session.execute_write(create_entity_node, ent["text"], ent["label"])
#                 session.execute_write(link_chunk_entity, chunk["chunk_id"], ent["text"])

#     print(f"Entity extraction and graph enrichment complete! Total chunks processed: {len(chunks)}")
