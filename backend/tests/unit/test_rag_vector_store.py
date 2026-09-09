"""Unit tests for PGVectorStore, Embeddings, and Tenant-Isolated RAG."""

from app.rag.embedding import LocalDenseEmbeddingProvider
from app.rag.vector_store import PGVectorStore, VectorDocument


def test_local_dense_embeddings():
    provider = LocalDenseEmbeddingProvider(dimension=384)
    v1 = provider.embed_text("Total sales revenue by customer")
    v2 = provider.embed_text("Total revenue from clients")
    v3 = provider.embed_text("Database connection timeout error")

    assert len(v1) == 384
    assert len(v2) == 384
    assert len(v3) == 384

    # Dot product / cosine similarity between v1 and v2 (semantically related) should be higher than v1 and v3
    sim_1_2 = sum(a * b for a, b in zip(v1, v2))
    sim_1_3 = sum(a * b for a, b in zip(v1, v3))
    assert sim_1_2 > sim_1_3


def test_vector_store_tenant_isolation():
    store = PGVectorStore()

    doc_biz_a = VectorDocument(
        id="doc-a1",
        business_id="biz_alpha",
        dataset_id="ds_1",
        document_type="table",
        title="Sales Table",
        content="Stores transactions for business Alpha.",
    )
    doc_biz_b = VectorDocument(
        id="doc-b1",
        business_id="biz_beta",
        dataset_id="ds_2",
        document_type="table",
        title="Sales Table",
        content="Stores transactions for business Beta.",
    )

    store.index_documents([doc_biz_a, doc_biz_b])

    # Search as Business Alpha
    results_alpha = store.search("transactions", business_id="biz_alpha")
    assert len(results_alpha) == 1
    assert results_alpha[0].document.business_id == "biz_alpha"
    assert results_alpha[0].document.id == "doc-a1"

    # Search as Business Beta
    results_beta = store.search("transactions", business_id="biz_beta")
    assert len(results_beta) == 1
    assert results_beta[0].document.business_id == "biz_beta"
    assert results_beta[0].document.id == "doc-b1"
