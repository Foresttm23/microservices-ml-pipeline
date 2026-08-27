from typing import Literal
from pydantic import Field
from shared.schemas import BaseSchema


class GraphState(BaseSchema):
    """Pydantic state model passed across all nodes in the LangGraph workflow."""

    question: str
    route: str = ""
    documents: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    generation: str = ""


class RouteDecision(BaseSchema):
    """Schema for LLM-based query classification / semantic routing."""

    route: Literal["retrieve", "direct_chat"] = Field(
        description="Choose 'retrieve' if the user asks about the creator, project details, architecture, or specific documentation. Choose 'direct_chat' for greetings or general conversational questions."
    )
