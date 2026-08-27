import os
from typing import Any, cast
from loguru import logger
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from langchain_core.documents import Document

from shared.core import ModelSettingsProtocol
from ml_worker.schemas.vector_store import RetrievedDoc


# Path to knowledge directory
KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge")
CREATOR_FILE_PATH = os.path.join(KNOWLEDGE_DIR, "about_creator.md")


def load_knowledge_documents() -> list[Document]:
    """Loads documents from knowledge directory with source metadata."""
    if os.path.exists(CREATOR_FILE_PATH):
        with open(CREATOR_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        return [
            Document(
                page_content=content,
                metadata={
                    "source": "ml_worker/knowledge/about_creator.md",
                    "title": "About Project Creator (Foresttm23)",
                    "topic": "author_profile",
                },
            )
        ]
    return [
        Document(
            page_content="Creator: Foresttm23. GitHub: https://github.com/Foresttm23. Built the ML Microservices Chat Pipeline.",
            metadata={"source": "ml_worker/knowledge/about_creator.md", "topic": "author_profile"},
        )
    ]


class VectorStoreService:
    """Manages the in-memory/persistent ChromaDB vector store and embeddings."""

    def __init__(
        self,
        settings: ModelSettingsProtocol,
        collection_name: str = "company_knowledge",
    ):
        self.collection_name = collection_name
        self._settings = settings

        # Use Chroma's built-in ONNX default embedding function (all-MiniLM-L6-v2)
        # Runs 100% locally and reliably without depending on external API embedding endpoints
        self._embedding_function = DefaultEmbeddingFunction()
        logger.info("VectorStore initialized with Chroma DefaultEmbeddingFunction (all-MiniLM-L6-v2)")

        self._client = chromadb.EphemeralClient(
            settings=Settings(anonymized_telemetry=False)
        )

        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._embedding_function,
            metadata={"hnsw:space": "cosine"},
        )
        self._seed_sample_documents()

    def _seed_sample_documents(self) -> None:
        """Populates the vector collection with initial sample documents."""
        count = self._collection.count()
        if count > 0:
            logger.debug("Collection '{}' already contains {} documents", self.collection_name, count)
            return

        docs = load_knowledge_documents()
        logger.info("Seeding {} document(s) into ChromaDB collection '{}'...", len(docs), self.collection_name)

        texts = [doc.page_content for doc in docs]
        metadatas: list[dict[Any, Any]] = [doc.metadata for doc in docs]
        ids = [f"doc_{i}" for i in range(len(docs))]

        try:
            # Chroma automatically handles embedding using the configured embedding_function
            self._collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,  # type: ignore[arg-type]
            )
            logger.info("Successfully seeded ChromaDB collection '{}'", self.collection_name)
        except Exception as exc:
            logger.exception("Failed to seed vector store: {}", exc)

    async def search(self, query: str, top_k: int = 3) -> list[RetrievedDoc]:
        """Asynchronously searches the vector store for the most relevant document chunks."""
        logger.debug("Querying vector store for: '{}'", query)
        try:
            # Chroma embeds the query string automatically via embedding_function
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
            )

            raw_docs = results.get("documents")
            raw_metas = results.get("metadatas")
            raw_dists = results.get("distances")

            documents = raw_docs[0] if raw_docs and len(raw_docs) > 0 else []
            metadatas = raw_metas[0] if raw_metas and len(raw_metas) > 0 else [{} for _ in documents]
            distances = raw_dists[0] if raw_dists and len(raw_dists) > 0 else [0.0] * len(documents)

            retrieved = []
            for doc, meta, dist in zip(documents, metadatas, distances):
                similarity_score = 1.0 - dist if dist is not None else 1.0
                retrieved.append(
                    RetrievedDoc(
                        content=doc or "",
                        metadata=dict(meta) if meta else {},
                        score=similarity_score,
                    )
                )

            logger.info("Vector search returned {} documents for query '{}'", len(retrieved), query)
            return retrieved
        except Exception as exc:
            logger.exception("Vector search failed: {}", exc)
            return []


# Global singleton instance helper
_vector_store_instance: VectorStoreService | None = None


def get_vector_store(settings: ModelSettingsProtocol) -> VectorStoreService:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreService(settings=settings)
    return _vector_store_instance
