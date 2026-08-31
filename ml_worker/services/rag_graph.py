from typing import Any
from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import RetryPolicy

from shared.core import ModelSettingsProtocol
from ml_worker.infra.vector_store import VectorStoreService
from ml_worker.schemas.rag import GraphState, RouteDecision


class RagGraphService:
    """Encapsulates the LangGraph RAG workflow and compiled StateGraph."""

    def __init__(self, settings: ModelSettingsProtocol, vector_store: VectorStoreService):
        self._settings = settings
        self._vector_store = vector_store
        self._llm = self._init_llm(settings)
        self._graph: CompiledStateGraph = self._build_graph()

    def _init_llm(self, settings: ModelSettingsProtocol) -> Any:
        """Initializes the chat LLM or returns None for dry-run."""
        if settings.API_KEY and not settings.ML_WORKER_DRY_RUN:
            max_retries = getattr(settings, "MAX_RETRIES", 3)
            return ChatGoogleGenerativeAI(
                model=settings.MODEL,
                google_api_key=settings.API_KEY,
                temperature=0.2,
                timeout=settings.TIMEOUT_SECONDS,
                max_retries=max_retries,
            )
        logger.warning("RagGraphService running in DRY_RUN / Mock mode (no API key)")
        return None

    def _build_graph(self) -> CompiledStateGraph:
        """Assembles the StateGraph nodes, edges, and conditional routing using Pydantic GraphState."""
        builder = StateGraph(GraphState)

        retry_policy = RetryPolicy(
            max_attempts=getattr(self._settings, "MAX_RETRIES", 3),
            initial_interval=1.0,
            backoff_factor=2.0,
        )

        # Add Nodes with retry policy
        builder.add_node("route_query", self._node_route_query, retry_policy=retry_policy)
        builder.add_node("retrieve", self._node_retrieve, retry_policy=retry_policy)
        builder.add_node("generate_grounded_answer", self._node_generate_grounded_answer, retry_policy=retry_policy)
        builder.add_node("direct_chat", self._node_direct_chat, retry_policy=retry_policy)

        # Connect Start -> Router
        builder.add_edge(START, "route_query")

        # Conditional Edge based on classification
        builder.add_conditional_edges(
            "route_query",
            self._decide_route,
            {
                "retrieve": "retrieve",
                "direct_chat": "direct_chat",
            },
        )

        # Retrieval -> Grounded generation -> END
        builder.add_edge("retrieve", "generate_grounded_answer")
        builder.add_edge("generate_grounded_answer", END)
        builder.add_edge("direct_chat", END)

        compiled = builder.compile()
        logger.info("LangGraph RAG StateGraph compiled successfully with Pydantic GraphState")
        return compiled

    async def _node_route_query(self, state: GraphState) -> dict[str, Any]:
        """Node 1: Classifies the user's intent to determine if retrieval is required."""
        question = state.question
        logger.debug("LangGraph: Routing question: '{}'", question)

        if not self._llm or self._settings.ML_WORKER_DRY_RUN:
            # Simple keyword heuristic fallback for dry-run or mock mode
            lower_q = question.lower()
            if any(k in lower_q for k in ["creator", "author", "foresttm23", "github", "who made", "project", "policy"]):
                return {"route": "retrieve"}
            return {"route": "direct_chat"}

        try:
            structured_router = self._llm.with_structured_output(RouteDecision)
            prompt = (
                f"Classify the following user query.\n"
                f"If it asks about the creator/author (Foresttm23), github, project details, documentation, or background, return 'retrieve'.\n"
                f"For general questions or casual chat, return 'direct_chat'.\n\n"
                f"User query: {question}"
            )
            decision: RouteDecision = await structured_router.ainvoke(prompt)
            route = decision.route
            logger.info("LangGraph router classified query as '{}'", route)
            return {"route": route}
        except Exception as exc:
            logger.warning("Router classification failed, defaulting to 'retrieve': {}", exc)
            return {"route": "retrieve"}

    @staticmethod
    def _decide_route(state: GraphState) -> str:
        """Conditional routing function inspecting the state's route field."""
        return state.route or "direct_chat"

    async def _node_retrieve(self, state: GraphState) -> dict[str, Any]:
        """Node 2: Queries ChromaDB vector store for relevant document chunks."""
        question = state.question
        logger.debug("LangGraph: Retrieving documents from ChromaDB for query: '{}'", question)

        retrieved_docs = await self._vector_store.search(query=question, top_k=3)
        documents = [doc.content for doc in retrieved_docs]
        sources = list({doc.metadata.get("source", "unknown") for doc in retrieved_docs if doc.metadata})

        logger.info("LangGraph retrieved {} document chunk(s) from ChromaDB", len(documents))
        return {
            "documents": documents,
            "sources": sources,
        }

    async def _node_generate_grounded_answer(self, state: GraphState) -> dict[str, Any]:
        """Node 3: Synthesizes a grounded answer using retrieved document context."""
        question = state.question
        documents = state.documents or []
        context = "\n\n---\n\n".join(documents) if documents else "No relevant context found."

        logger.debug("LangGraph: Generating grounded answer with {} context chunks", len(documents))

        if not self._llm or self._settings.ML_WORKER_DRY_RUN:
            return {
                "generation": f"[dry-run] Grounded answer for '{question}' based on: {state.sources}"
            }

        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful and knowledgeable AI assistant for the ML Microservices project.\n"
                    "Answer the user's question accurately using ONLY the provided context.\n"
                    "If the context does not contain enough information to answer, state that politely.\n\n"
                    "Rules:\n"
                    "- Always return only text, do not include any thoughts or constraints.\n"
                    "Context:\n{context}",
                ),
                ("human", "{question}"),
            ]
        )

        chain = prompt_template | self._llm
        response = await chain.ainvoke({"context": context, "question": question})
        content = response.content if hasattr(response, "content") else str(response)

        return {"generation": str(content)}

    async def _node_direct_chat(self, state: GraphState) -> dict[str, Any]:
        """Node 4: Answers conversational queries directly without document retrieval."""
        question = state.question
        logger.debug("LangGraph: Generating direct chat response for: '{}'", question)

        if not self._llm or self._settings.ML_WORKER_DRY_RUN:
            return {"generation": f"[dry-run] Direct response for: {question}", "sources": []}

        messages = [
            SystemMessage(
                content="You are a helpful and friendly AI assistant. Engage the user directly and concisely."
            ),
            HumanMessage(content=question),
        ]
        response = await self._llm.ainvoke(messages)
        content = response.content if hasattr(response, "content") else str(response)

        return {"generation": str(content), "sources": []}

    async def ainvoke(self, question: str) -> dict[str, Any]:
        """Executes the compiled LangGraph workflow end-to-end for a given question."""
        initial_state = GraphState(question=question)
        result = await self._graph.ainvoke(initial_state)
        # Convert result to dict if it's a Pydantic model
        if isinstance(result, GraphState):
            return result.model_dump()
        return result
