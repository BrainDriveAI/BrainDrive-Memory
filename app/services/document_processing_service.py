import uuid
import hashlib
from datetime import datetime
from neo4j import GraphDatabase
from llmsherpa.readers import LayoutPDFReader

from app.services.pdf_processing_service import upload_file_to_gcs
from app.adapters.embedder_adapter import embedder
from app.config.app_env import app_env

# Neo4j configuration
NEO4J_URL = app_env.NEO4J_URL
NEO4J_USER = app_env.NEO4J_USER
NEO4J_PASSWORD = app_env.NEO4J_PWD.get_secret_value()
NEO4J_DATABASE = "neo4j"


def get_embedding(text: str) -> list:
    """Generate an embedding for the given text using llmsherpa's OpenAIEmbeddings."""
    return embedder.embed_query(text)


# File location for PDFs
file_location = '/home/QA/Neo4j_Stage1/PDFs'


def initialiseNeo4j():
    cypher_schema = [
        "CREATE CONSTRAINT sectionKey IF NOT EXISTS FOR (c:Section) REQUIRE (c.key) IS UNIQUE;",
        "CREATE CONSTRAINT chunkKey IF NOT EXISTS FOR (c:Chunk) REQUIRE (c.key) IS UNIQUE;",
        "CREATE CONSTRAINT documentKey IF NOT EXISTS FOR (c:Document) REQUIRE (c.url_hash) IS UNIQUE;",
        "CREATE CONSTRAINT tableKey IF NOT EXISTS FOR (c:Table) REQUIRE (c.key) IS UNIQUE;",
        # Drop the old vector index and create a new one on Chunk nodes using the 'embedding' property.
        "CALL db.index.vector.dropNodeIndex('chunkVectorIndex') YIELD name RETURN name;",
        "CALL db.index.vector.createNodeIndex('chunkVectorIndex', 'Chunk', 'embedding', 1024, 'COSINE')"
    ]
    driver = GraphDatabase.driver(NEO4J_URL, database=NEO4J_DATABASE, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        for cypher in cypher_schema:
            try:
                session.run(cypher)
            except Exception as e:
                print(f"Error running cypher: {cypher}\nError: {e}")
    driver.close()


def ingestDocumentNeo4j(doc, file_name, doc_url):
    """
    Ingests a parsed PDF document into Neo4j.
    For each Document, Section, Chunk, and Table, an embedding is generated and stored.
    """
    cypher_pool = [
        # Document node creation with embedding (document embedding computed from concatenating section titles)
        "MERGE (d:Document {name: $doc_name_val}) ON CREATE SET d.url = $doc_url_val, d.embedding = $doc_embedding RETURN d;",
        # Section creation with embedding
        "MERGE (p:Section {key: $doc_name_val+'|'+$block_idx_val+'|'+$title_hash_val}) ON CREATE SET p.page_idx = $page_idx_val, p.title_hash = $title_hash_val, p.block_idx = $block_idx_val, p.title = $title_val, p.tag = $tag_val, p.level = $level_val, p.embedding = $sec_embedding RETURN p;",
        "MATCH (d:Document {name: $doc_name_val}) MATCH (s:Section {key: $doc_name_val+'|'+$block_idx_val+'|'+$title_hash_val}) MERGE (d)<-[:HAS_DOCUMENT]-(s);",
        "MATCH (s1:Section {key: $doc_name_val+'|'+$parent_block_idx_val+'|'+$parent_title_hash_val}) MATCH (s2:Section {key: $doc_name_val+'|'+$block_idx_val+'|'+$title_hash_val}) MERGE (s1)<-[:UNDER_SECTION]-(s2);",
        # Chunk creation with embedding
        "MERGE (c:Chunk {key: $doc_name_val+'|'+$block_idx_val+'|'+$sentences_hash_val}) ON CREATE SET c.sentences = $sentences_val, c.sentences_hash = $sentences_hash_val, c.block_idx = $block_idx_val, c.page_idx = $page_idx_val, c.tag = $tag_val, c.level = $level_val, c.embedding = $chunk_embedding RETURN c;",
        "MATCH (c:Chunk {key: $doc_name_val+'|'+$block_idx_val+'|'+$sentences_hash_val}) MATCH (s:Section {key:$doc_name_val+'|'+$parent_block_idx_val+'|'+$parent_hash_val}) MERGE (s)<-[:HAS_PARENT]-(c);",
        # Table creation with embedding (using table html as text)
        "MERGE (t:Table {key: $doc_name_val+'|'+$block_idx_val+'|'+$name_val}) ON CREATE SET t.name = $name_val, t.doc_name = $doc_name_val, t.block_idx = $block_idx_val, t.page_idx = $page_idx_val, t.html = $html_val, t.rows = $rows_val, t.embedding = $table_embedding RETURN t;",
        "MATCH (t:Table {key: $doc_name_val+'|'+$block_idx_val+'|'+$name_val}) MATCH (s:Section {key: $doc_name_val+'|'+$parent_block_idx_val+'|'+$parent_hash_val}) MERGE (s)<-[:HAS_PARENT]-(t);",
        "MATCH (t:Table {key: $doc_name_val+'|'+$block_idx_val+'|'+$name_val}) MATCH (s:Document {name: $doc_name_val}) MERGE (s)<-[:HAS_PARENT]-(t);"
    ]

    driver = GraphDatabase.driver(NEO4J_URL, database=NEO4J_DATABASE, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        doc_name_val = file_name
        doc_url_val = doc_url

        # Compute document full text (using section titles as a proxy) and its embedding.
        sections = list(doc.sections())
        chunks = list(doc.chunks())
        doc_full_text = ""
        if sections:
            doc_full_text = "\n".join([sec.title for sec in sections])
        elif chunks:
            doc_full_text = "\n".join(["\n".join(chunk.sentences) for chunk in chunks])
        print(doc_full_text)
        doc_embedding = get_embedding(doc_full_text)

        # Create the Document node.
        cypher = cypher_pool[0]
        session.run(cypher, doc_name_val=doc_name_val, doc_url_val=doc_url_val, doc_embedding=doc_embedding)

        # Check if any sections were identified.
        
        if not sections:
            # No sections were identified; create a default section.
            default_section_key = f"{doc_name_val}|default|default"
            default_section_title = f"Default Section"
            default_sec_embedding = get_embedding(default_section_title)
            cypher_default = (
                "MERGE (p:Section {key: $default_section_key}) "
                "ON CREATE SET p.page_idx = 0, p.title = $default_section_title, p.tag = 'default', p.level = 0, p.embedding = $default_sec_embedding "
                "RETURN p;"
            )
            session.run(cypher_default, default_section_key=default_section_key,
                        default_section_title=default_section_title,
                        default_sec_embedding=default_sec_embedding)
            # For later linking, set a variable to use as the parent key.
            parent_key_for_chunks = default_section_key
        else:
            parent_key_for_chunks = None  # We'll use normal parent linking if sections exist

        # Process Sections
        for sec in sections:
            sec_title_val = sec.title
            sec_title_hash_val = hashlib.md5(sec_title_val.encode("utf-8")).hexdigest()
            sec_tag_val = sec.tag
            sec_level_val = sec.level
            sec_page_idx_val = sec.page_idx
            sec_block_idx_val = sec.block_idx

            # Compute section embedding.
            sec_embedding = get_embedding(sec_title_val)

            if sec_tag_val != 'table':
                cypher = cypher_pool[1]
                session.run(cypher,
                            page_idx_val=sec_page_idx_val,
                            title_hash_val=sec_title_hash_val,
                            title_val=sec_title_val,
                            tag_val=sec_tag_val,
                            level_val=sec_level_val,
                            block_idx_val=sec_block_idx_val,
                            doc_name_val=doc_name_val,
                            sec_embedding=sec_embedding)

                sec_parent_val = str(sec.parent.to_text())
                if sec_parent_val == "None":
                    cypher = cypher_pool[2]
                    session.run(cypher,
                                page_idx_val=sec_page_idx_val,
                                title_hash_val=sec_title_hash_val,
                                doc_name_val=doc_name_val,
                                block_idx_val=sec_block_idx_val)
                else:
                    sec_parent_title_hash_val = hashlib.md5(sec_parent_val.encode("utf-8")).hexdigest()
                    cypher = cypher_pool[3]
                    session.run(cypher,
                                page_idx_val=sec_page_idx_val,
                                title_hash_val=sec_title_hash_val,
                                block_idx_val=sec_block_idx_val,
                                parent_title_hash_val=sec_parent_title_hash_val,
                                parent_block_idx_val=sec.parent.block_idx,
                                doc_name_val=doc_name_val)

        # Process Chunks
        for chk in doc.chunks():
            chunk_block_idx_val = chk.block_idx
            chunk_page_idx_val = chk.page_idx
            chunk_tag_val = chk.tag
            chunk_level_val = chk.level
            chunk_sentences = "\n".join(chk.sentences)
            # Compute chunk embedding.
            chunk_embedding = get_embedding(chunk_sentences)

            if chunk_tag_val != 'table':
                chunk_sentences_hash_val = hashlib.md5(chunk_sentences.encode("utf-8")).hexdigest()
                cypher = cypher_pool[4]
                session.run(cypher,
                            sentences_hash_val=chunk_sentences_hash_val,
                            sentences_val=chunk_sentences,
                            block_idx_val=chunk_block_idx_val,
                            page_idx_val=chunk_page_idx_val,
                            tag_val=chunk_tag_val,
                            level_val=chunk_level_val,
                            doc_name_val=doc_name_val,
                            chunk_embedding=chunk_embedding)

                chk_parent_val = str(chk.parent.to_text())
                if chk_parent_val != "None":
                    chk_parent_hash_val = hashlib.md5(chk_parent_val.encode("utf-8")).hexdigest()
                    cypher = cypher_pool[5]
                    session.run(cypher,
                                sentences_hash_val=chunk_sentences_hash_val,
                                block_idx_val=chunk_block_idx_val,
                                parent_hash_val=chk_parent_hash_val,
                                parent_block_idx_val=chk.parent.block_idx,
                                doc_name_val=doc_name_val)
                elif parent_key_for_chunks is not None:
                    # If no parent was identified and we have a default section, attach chunk to it.
                    cypher_link_default = (
                        "MATCH (c:Chunk {key: $doc_name_val+'|'+$block_idx_val+'|'+$sentences_hash_val}), "
                        "(s:Section {key: $default_section_key}) "
                        "MERGE (s)<-[:HAS_PARENT]-(c);"
                    )
                    session.run(cypher_link_default,
                                doc_name_val=doc_name_val,
                                block_idx_val=chunk_block_idx_val,
                                sentences_hash_val=chunk_sentences_hash_val,
                                default_section_key=parent_key_for_chunks)

        # Process Tables
        for tb in doc.tables():
            page_idx_val = tb.page_idx
            block_idx_val = tb.block_idx
            name_val = 'block#' + str(block_idx_val) + '_' + tb.name
            html_val = tb.to_html()
            rows_val = len(tb.rows)
            # Compute table embedding from the HTML content.
            table_embedding = get_embedding(html_val)
            cypher = cypher_pool[6]
            session.run(cypher,
                        block_idx_val=block_idx_val,
                        page_idx_val=page_idx_val,
                        name_val=name_val,
                        html_val=html_val,
                        rows_val=rows_val,
                        doc_name_val=doc_name_val,
                        table_embedding=table_embedding)

            table_parent_val = str(tb.parent.to_text())
            if table_parent_val != "None":
                table_parent_hash_val = hashlib.md5(table_parent_val.encode("utf-8")).hexdigest()
                cypher = cypher_pool[7]
                session.run(cypher,
                            name_val=name_val,
                            block_idx_val=block_idx_val,
                            parent_page_idx_val=tb.parent.page_idx,
                            parent_hash_val=table_parent_hash_val,
                            parent_block_idx_val=tb.parent.block_idx,
                            doc_name_val=doc_name_val)
            else:
                cypher = cypher_pool[8]
                session.run(cypher,
                            name_val=name_val,
                            block_idx_val=block_idx_val,
                            doc_name_val=doc_name_val)

        print(f"'{doc_name_val}' Done! Summary: ")
        print('#Sections: ' + str(len(doc.sections())))
        print('#Chunks: ' + str(len(doc.chunks())))
        print('#Tables: ' + str(len(doc.tables())))
    driver.close()


def parseAndIngestPDFs(pdf_file_path: str, file_name: str, bucket_name: str):
    file_id = str(uuid.uuid4())
    # Upload file to Google Cloud Storage
    destination_blob_name = f"uploads/{file_id}_{file_name}"
    cloud_url = upload_file_to_gcs(pdf_file_path, bucket_name, destination_blob_name)
    pdf_reader = LayoutPDFReader(app_env.LLM_SHERPA_API_URL)
    startTime = datetime.now()

    try:
        doc = pdf_reader.read_pdf(cloud_url)
        ingestDocumentNeo4j(doc, file_name, cloud_url)
        print(f"Total time: {datetime.now() - startTime}")
    except Exception as e:
        print(f"Error processing PDF file {file_name}: {e}")

# Initialize Neo4j and ingest PDFs
# initialiseNeo4j()
# parseAndIngestPDFs()


# --- Search Method ---
def search_by_embedding(query: str, top_k: int = 50):
    """
    Computes the embedding for the query and retrieves the top_k nodes (across all types)
    that have an 'embedding' property, sorted by cosine similarity.
    """
    query_embedding = get_embedding(query)
    driver = GraphDatabase.driver(NEO4J_URL, database=NEO4J_DATABASE, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        cypher_query = """
            MATCH (c:Chunk)
            WHERE c.embedding IS NOT NULL
            WITH c,
                round(reduce(dot = 0.0, i IN range(0, size(c.embedding)-1) | dot + c.embedding[i] * $n_embedding[i]) /
                (sqrt(reduce(l2 = 0.0, i IN range(0, size(c.embedding)-1) | l2 + c.embedding[i] * c.embedding[i])) *
                sqrt(reduce(l2 = 0.0, i IN range(0, size($n_embedding)-1) | l2 + $n_embedding[i] * $n_embedding[i]))), 4) AS similarity
            WHERE similarity >= $threshold
            MATCH (s:Section)<-[:HAS_PARENT]-(c)
            OPTIONAL MATCH (d:Document)<-[:HAS_DOCUMENT]-(s)
            RETURN d.name AS source, d.url AS source_url, elementId(d) AS source_id, s.title AS section, c.sentences AS chunk, similarity, elementId(c) AS chunk_id
            ORDER BY similarity DESC
            LIMIT $top_k
        """
        result = session.run(
            cypher_query,
            n_embedding=query_embedding,
            threshold=0.7,
            top_k=top_k
        )
        results = []
        for item in result:
            results.append({
                "document_url": item["source_url"],
                "document": item["source"],
                "document_id": item["source_id"],
                "section": item["section"],
                "sentences": item["chunk"],
            })
    driver.close()
    return results


def search_for_all_documents(query: str):
    cypher_query = """
        MATCH (d:Document)
        RETURN d.name AS source, d.url AS document_url, elementId(d) AS source_id
        ORDER BY d.name
    """
    driver = GraphDatabase.driver(NEO4J_URL, database=NEO4J_DATABASE, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run(cypher_query)
        results = []
        for item in result:
            results.append({
                "document_url": item["document_url"],
                "document": item["source"],
                "document_id": item["source_id"],
            })
    driver.close()
    return results

# Example search usage
# if __name__ == "__main__":
#     search_query = "Relevant content about work documents"
#     results = search_by_embedding(search_query, top_k=5)
#     print("Search Results:")
#     for node, similarity in results:
#         print("Node:", node)
#         print("Similarity:", similarity)
#         print("-----")
