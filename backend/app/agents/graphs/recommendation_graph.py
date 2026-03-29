"""
LangGraph state machine for Recommendation Agent.
"""
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from app.agents.base import BaseAgent
from app.agents.utils import format_user_profile, format_product_list_for_prompt, parse_groq_json_scores
import structlog


logger = structlog.get_logger()


class RecommendationState(TypedDict):
    """State for recommendation workflow."""
    user_id: str
    user_profile: Dict[str, Any]
    candidate_products: List[Dict[str, Any]]
    scored_products: List[Dict[str, Any]]
    final_recommendations: List[Dict[str, Any]]
    error: Optional[str]


class RecommendationGraph(BaseAgent):
    """LangGraph implementation of Recommendation Agent."""

    def __init__(self):
        """Initialize recommendation agent."""
        super().__init__()
        self.logger = logger.bind(agent="recommendation")
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build LangGraph state machine."""
        graph = StateGraph(RecommendationState)

        # Add nodes
        graph.add_node("score_products", self._score_products_node)
        graph.add_node("rank_and_select", self._rank_and_select_node)
        graph.add_node("format_output", self._format_output_node)

        # Add edges
        graph.add_edge("score_products", "rank_and_select")
        graph.add_edge("rank_and_select", "format_output")
        graph.add_edge("format_output", END)

        # Set start node
        graph.set_entry_point("score_products")

        return graph.compile()

    async def _score_products_node(self, state: RecommendationState) -> RecommendationState:
        """Score each product based on user profile."""
        self.logger.info("scoring_products", count=len(state["candidate_products"]))

        user_profile = format_user_profile(state["user_profile"])
        products_text = format_product_list_for_prompt(state["candidate_products"])

        prompt = f"""You are a recommendation engine. Score these products for the user.

{user_profile}

Products:
{products_text}

For each product, provide a score from 0 to 1 based on how well it matches the user's interests.

Return a JSON array with this structure:
[
  {{"product_name": "...", "score": 0.85, "reasoning": "..."}},
  ...
]

Only return the JSON array, no other text."""

        response = await self.call_groq_json(prompt)

        if response is None:
            state["error"] = "Failed to get GROQ response for scoring products"
            return state

        # Ensure response is a list
        scored = response if isinstance(response, list) else [response]

        state["scored_products"] = scored
        self.logger.info("products_scored", count=len(scored))

        return state

    async def _rank_and_select_node(self, state: RecommendationState) -> RecommendationState:
        """Rank products and select top 10."""
        self.logger.info("ranking_products", count=len(state["scored_products"]))

        # Sort by score (descending)
        sorted_products = sorted(
            state["scored_products"],
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        # Select top 10
        top_products = sorted_products[:10]

        state["final_recommendations"] = top_products
        self.logger.info("products_ranked", total=len(sorted_products), selected=len(top_products))

        return state

    async def _format_output_node(self, state: RecommendationState) -> RecommendationState:
        """Format final recommendations for output."""
        self.logger.info("formatting_output", count=len(state["final_recommendations"]))
        # Output is already in correct format
        return state

    async def execute_for_user(self, user_id: str, user_profile: Dict[str, Any], candidate_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute recommendation graph for a user."""
        self.logger.info("executing_recommendation_agent", user_id=user_id)

        initial_state: RecommendationState = {
            "user_id": user_id,
            "user_profile": user_profile,
            "candidate_products": candidate_products,
            "scored_products": [],
            "final_recommendations": [],
            "error": None,
        }

        try:
            result = await self._async_invoke(initial_state)
            return result
        except Exception as e:
            self.logger.error("agent_execution_failed", error=str(e))
            return {"error": str(e), "final_recommendations": []}

    async def _async_invoke(self, initial_state: RecommendationState) -> Dict[str, Any]:
        """Invoke graph asynchronously."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.graph.invoke, initial_state)
