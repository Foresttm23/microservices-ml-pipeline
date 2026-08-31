import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ml_worker.core.config import GeminiSettings
from ml_worker.schemas.rag import GraphState, RouteDecision
from ml_worker.schemas.vector_store import RetrievedDoc
from ml_worker.services.rag_graph import RagGraphService


@pytest.fixture
def mock_vector_store():
    store = MagicMock()
    store.search = AsyncMock(
        return_value=[
            RetrievedDoc(
                content="Foresttm23 is the creator of the repository.",
                metadata={"source": "about_creator.md"},
                score=0.95,
            )
        ]
    )
    return store


def test_rag_graph_service_initialization_with_retry_policy(mock_vector_store):
    settings = GeminiSettings(
        API_KEY="mock-key",
        MAX_RETRIES=3,
        ML_WORKER_DRY_RUN=True,
    )
    service = RagGraphService(settings=settings, vector_store=mock_vector_store)

    assert service._graph is not None
    nodes = service._graph.nodes
    assert "route_query" in nodes
    assert "retrieve" in nodes
    assert "generate_grounded_answer" in nodes
    assert "direct_chat" in nodes


@pytest.mark.asyncio
async def test_rag_graph_service_ainvoke_dry_run_direct_chat(mock_vector_store):
    settings = GeminiSettings(
        API_KEY=None,
        ML_WORKER_DRY_RUN=True,
    )
    service = RagGraphService(settings=settings, vector_store=mock_vector_store)
    result = await service.ainvoke("Hello world")

    assert "generation" in result
    assert result["route"] == "direct_chat"


@pytest.mark.asyncio
async def test_rag_graph_service_ainvoke_dry_run_retrieve_route(mock_vector_store):
    settings = GeminiSettings(
        API_KEY=None,
        ML_WORKER_DRY_RUN=True,
    )
    service = RagGraphService(settings=settings, vector_store=mock_vector_store)
    result = await service.ainvoke("Who is the creator Foresttm23?")

    assert "generation" in result
    assert result["route"] == "retrieve"
    assert "about_creator.md" in result["sources"]


@pytest.mark.asyncio
async def test_node_route_query_with_llm(mock_vector_store):
    settings = GeminiSettings(
        API_KEY="real-key",
        ML_WORKER_DRY_RUN=False,
    )
    with patch("ml_worker.services.rag_graph.ChatGoogleGenerativeAI"):
        service = RagGraphService(settings=settings, vector_store=mock_vector_store)
        
        # Mock structured router
        mock_router = MagicMock()
        mock_router.ainvoke = AsyncMock(return_value=RouteDecision(route="retrieve"))
        service._llm.with_structured_output = MagicMock(return_value=mock_router)

        state = GraphState(question="Explain the project architecture")
        result = await service._node_route_query(state)
        assert result["route"] == "retrieve"


@pytest.mark.asyncio
async def test_node_route_query_llm_failure_fallback(mock_vector_store):
    settings = GeminiSettings(
        API_KEY="real-key",
        ML_WORKER_DRY_RUN=False,
    )
    with patch("ml_worker.services.rag_graph.ChatGoogleGenerativeAI"):
        service = RagGraphService(settings=settings, vector_store=mock_vector_store)
        
        mock_router = MagicMock()
        mock_router.ainvoke = AsyncMock(side_effect=Exception("API error"))
        service._llm.with_structured_output = MagicMock(return_value=mock_router)

        state = GraphState(question="Any question")
        result = await service._node_route_query(state)
        assert result["route"] == "retrieve"


@pytest.mark.asyncio
async def test_node_retrieve(mock_vector_store):
    settings = GeminiSettings(ML_WORKER_DRY_RUN=True)
    service = RagGraphService(settings=settings, vector_store=mock_vector_store)

    state = GraphState(question="Who is Foresttm23?", route="retrieve")
    result = await service._node_retrieve(state)

    assert "documents" in result
    assert len(result["documents"]) == 1
    assert "about_creator.md" in result["sources"]
    mock_vector_store.search.assert_called_once()


@pytest.mark.asyncio
async def test_node_generate_grounded_answer_with_llm(mock_vector_store):
    settings = GeminiSettings(
        API_KEY="real-key",
        ML_WORKER_DRY_RUN=False,
    )
    with patch("ml_worker.services.rag_graph.ChatGoogleGenerativeAI"):
        service = RagGraphService(settings=settings, vector_store=mock_vector_store)
        
        state = GraphState(
            question="Who created this?",
            documents=["Foresttm23 created this repo."],
            sources=["about_creator.md"],
            route="retrieve",
        )
        
        mock_response = MagicMock()
        mock_response.content = "Foresttm23 is the author."
        
        with patch("langchain_core.prompts.ChatPromptTemplate.__or__") as mock_chain:
            mock_runnable = MagicMock()
            mock_runnable.ainvoke = AsyncMock(return_value=mock_response)
            mock_chain.return_value = mock_runnable

            result = await service._node_generate_grounded_answer(state)
            assert result["generation"] == "Foresttm23 is the author."


@pytest.mark.asyncio
async def test_node_direct_chat_with_llm(mock_vector_store):
    settings = GeminiSettings(
        API_KEY="real-key",
        ML_WORKER_DRY_RUN=False,
    )
    with patch("ml_worker.services.rag_graph.ChatGoogleGenerativeAI"):
        service = RagGraphService(settings=settings, vector_store=mock_vector_store)
        
        mock_response = MagicMock()
        mock_response.content = "I am doing well, thanks!"
        service._llm.ainvoke = AsyncMock(return_value=mock_response)

        state = GraphState(question="How are you?", route="direct_chat")
        result = await service._node_direct_chat(state)

        assert result["generation"] == "I am doing well, thanks!"
        assert result["sources"] == []
