"""
Recommendation Agent orchestration and database persistence.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.graphs.recommendation_graph import RecommendationGraph
from app.models.recommendation import Recommendation
from app.models.product import Product
from app.models.user import User, UserPreference
from app.services.product_service import ProductService
import structlog


logger = structlog.get_logger()


class RecommendationAgentOrchestrator:
    """Orchestrate recommendation generation and persistence."""

    def __init__(self, db: AsyncSession):
        """Initialize orchestrator."""
        self.db = db
        self.graph = RecommendationGraph()
        self.product_service = ProductService(db)
        self.logger = logger.bind(service="recommendation_agent_orchestrator")

    async def generate_recommendations_for_user(self, user_id: UUID) -> Dict[str, Any]:
        """Generate and persist recommendations for a user."""
        self.logger.info("generating_recommendations", user_id=user_id)

        try:
            # Fetch user
            user = await self.db.get(User, user_id)
            if not user or not user.is_active:
                self.logger.warning("user_not_found_or_inactive", user_id=user_id)
                return {"error": "User not found or inactive", "recommendations": []}

            # Fetch user preferences
            from sqlalchemy import select
            result = await self.db.execute(
                select(UserPreference).where(UserPreference.user_id == user_id)
            )
            preferences = result.scalars().all()

            if not preferences:
                self.logger.info("no_preferences_found", user_id=user_id)
                return {"error": "user has no preference", "recommendations": []}

            # Get candidate products based on preferences
            categories = [p.category for p in preferences if p.category]
            candidate_products = []

            for category in categories:
                products = await self.product_service.get_products_by_category(category, limit=50)
                candidate_products.extend([self._product_to_dict(p) for p in products])

            if not candidate_products:
                self.logger.info("no_candidate_products_found", categories=categories)
                return {"error": "No candidate products found", "recommendations": []}

            # Remove duplicates
            seen_ids = set()
            unique_products = []
            for p in candidate_products:
                if p["id"] not in seen_ids:
                    seen_ids.add(p["id"])
                    unique_products.append(p)

            # Run recommendation graph
            user_profile = {
                "age": user.age,
                "interests": [p.category for p in preferences],
            }

            result = await self.graph.execute_for_user(
                str(user_id),
                user_profile,
                unique_products[:100]  # Limit to 100 products for performance
            )

            if "error" in result:
                self.logger.error("graph_execution_failed", error=result["error"])
                return result

            # Persist recommendations
            recommendations = await self._persist_recommendations(
                user_id,
                result["final_recommendations"],
                unique_products
            )

            self.logger.info("recommendations_generated", user_id=user_id, count=len(recommendations))
            return {"recommendations": recommendations, "count": len(recommendations)}

        except Exception as e:
            self.logger.error("error_generating_recommendations", error=str(e))
            return {"error": str(e), "recommendations": []}

    async def _persist_recommendations(
        self,
        user_id: UUID,
        scored_products: List[Dict[str, Any]],
        all_products: List[Dict[str, Any]],
    ) -> List[Recommendation]:
        """Persist recommendations to database."""
        from sqlalchemy import select, and_

        recommendations = []
        expires_at = datetime.utcnow() + timedelta(hours=4)

        # Map product names to product objects
        product_map = {p["id"]: p for p in all_products}

        for item in scored_products[:10]:  # Top 10 recommendations
            product_name = item.get("product_name", "")
            score = Decimal(str(item.get("score", 0)))
            reasoning = item.get("reasoning", "N/A")

            # Find product by name
            result = await self.db.execute(
                select(Product).where(
                    Product.name.ilike(f"%{product_name}%")
                ).limit(1)
            )
            product = result.scalar_one_or_none()

            if not product:
                self.logger.warning("product_not_found_for_recommendation", product_name=product_name)
                continue

            # Check if recommendation already exists
            result = await self.db.execute(
                select(Recommendation).where(
                    and_(
                        Recommendation.user_id == user_id,
                        Recommendation.product_id == product.id,
                        Recommendation.expires_at > datetime.utcnow()
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing recommendation
                existing.score = score
                existing.reasoning = reasoning
                existing.generated_at = datetime.utcnow()
                existing.expires_at = expires_at
            else:
                # Create new recommendation
                recommendation = Recommendation(
                    user_id=user_id,
                    product_id=product.id,
                    score=score,
                    reasoning=reasoning,
                    generated_at=datetime.utcnow(),
                    expires_at=expires_at,
                    shown_to_user=False,
                )
                self.db.add(recommendation)
                recommendations.append(recommendation)

        await self.db.commit()
        self.logger.info("recommendations_persisted", count=len(recommendations))

        return recommendations

    def _product_to_dict(self, product: Product) -> Dict[str, Any]:
        """Convert product ORM object to dict."""
        return {
            "id": str(product.id),
            "name": product.name,
            "category": product.category or "Uncategorized",
            "price": product.current_price,
            "rating": product.rating,
            "reviews": product.reviews_count or 0,
            "brand": product.brand or "Unknown",
            "platform": product.platform,
        }
