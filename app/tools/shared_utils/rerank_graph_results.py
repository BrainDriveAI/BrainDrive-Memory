import logging
from nltk.tokenize import word_tokenize
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from app.utils.milis_to_str import millis_to_str

logger = logging.getLogger(__name__)

def rerank_graph_results(search_results, query, top_k: int = 3):
    # 1) Sort by most recent
    sorted_results = sorted(
        search_results,
        key=lambda e: e.get('updated_at', 0),
        reverse=True
    )

    # 2) Build Documents with readable timestamps
    edge_docs = []
    for e in sorted_results:
        try:
            created = millis_to_str(e["created_at"])
            updated = millis_to_str(e["updated_at"])
        except Exception:
            # fallback if timestamps missing or malformed
            created = updated = "unknown"
        text = (
            f"{e['source']} → {e['relationship'].replace('_',' ')} → "
            f"{e['destination'].replace('_',' ')} "
            f"(created: {created}, updated: {updated})"
        )
        edge_docs.append(Document(page_content=text, metadata=e))

    # if no docs to rank, return an empty list
    if not edge_docs:
        return []

    # 3) BM25 re-ranking with error handling
    try:
        keyword_retriever = BM25Retriever.from_documents(
            edge_docs,
            k=top_k,
            preprocess_func=word_tokenize,
        )
        best_docs = keyword_retriever.invoke(query)
        return [doc.page_content for doc in best_docs]
    except Exception as err:
        logger.error("BM25 rerank failed, falling back to timestamp order", exc_info=err)
        # fallback: return the top_k items by timestamp
        return [
            (
                f"{e['source']} → {e['relationship'].replace('_',' ')} → "
                f"{e['destination'].replace('_',' ')}"
            )
            for e in sorted_results[:top_k]
        ]
