import pytest
from unittest.mock import MagicMock, patch

from ml_worker.core.config import GeminiSettings
from ml_worker.infra.vector_store import (
    VectorStoreService,
    get_vector_store,
    load_knowledge_documents,
)


def test_load_knowledge_documents():
    docs = load_knowledge_documents()
    assert len(docs) > 0
    assert docs[0].page_content != ""
    assert "source" in docs[0].metadata


def test_vector_store_service_init_and_seeding():
    settings = GeminiSettings(ML_WORKER_DRY_RUN=True)
    service = VectorStoreService(settings=settings, collection_name="test_collection")

    assert service._collection is not None
    assert service._collection.count() > 0


@pytest.mark.asyncio
async def test_vector_store_service_search():
    settings = GeminiSettings(ML_WORKER_DRY_RUN=True)
    service = VectorStoreService(settings=settings, collection_name="test_search_collection")

    results = await service.search("Foresttm23", top_k=2)
    assert len(results) > 0
    assert results[0].content != ""
    assert results[0].score is not None


@pytest.mark.asyncio
async def test_vector_store_service_search_handles_exception():
    settings = GeminiSettings(ML_WORKER_DRY_RUN=True)
    service = VectorStoreService(settings=settings, collection_name="test_exc_collection")

    with patch.object(service._collection, "query", side_effect=Exception("Chroma error")):
        results = await service.search("test", top_k=1)
        assert results == []


def test_get_vector_store_singleton():
    settings = GeminiSettings(ML_WORKER_DRY_RUN=True)
    store1 = get_vector_store(settings)
    store2 = get_vector_store(settings)
    assert store1 is store2
