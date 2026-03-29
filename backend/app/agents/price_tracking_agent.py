"""
Price Tracking Agent for detecting significant price changes.
"""
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent
from app.agents.utils import calculate_price_percentage_change
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.models.price_alert import PriceAlert
from app.models.notification import Notification
import structlog


logger = structlog.get_logger()


class PriceTrackingAgent(BaseAgent):
    """Agent for tracking price changes and triggering alerts."""

    def __init__(self, db: AsyncSession):
        """Initialize price tracking agent."""
        super().__init__()
        self.db = db
        self.logger = logger.bind(agent="price_tracking")

    async def run(self) -> Dict[str, Any]:
        """Execute price tracking workflow."""
        self.logger.info("price_tracking_agent_started")

        try:
            # Fetch all active price alerts
            result = await self.db.execute(
                select(PriceAlert).where(PriceAlert.is_active == True)
            )
            alerts = result.scalars().all()

            self.logger.info("loaded_active_alerts", count=len(alerts))

            triggered_alerts = []

            for alert in alerts:
                product_id = alert.product_id

                # Fetch recent prices (last 2 prices)
                result = await self.db.execute(
                    select(PriceHistory)
                    .where(PriceHistory.product_id == product_id)
                    .order_by(desc(PriceHistory.recorded_at))
                    .limit(2)
                )
                prices = result.scalars().all()

                if len(prices) < 2:
                    continue

                old_price = prices[1].price  # Second most recent
                new_price = prices[0].price  # Most recent

                # Calculate percentage change
                pct_change = calculate_price_percentage_change(old_price, new_price)

                # Check if alert should trigger
                if await self._should_trigger_alert(alert, new_price, pct_change):
                    triggered_alerts.append({
                        "alert_id": alert.id,
                        "product_id": product_id,
                        "user_id": alert.user_id,
                        "old_price": old_price,
                        "new_price": new_price,
                        "pct_change": pct_change,
                    })

                    # Mark alert as triggered
                    alert.triggered_at = datetime.utcnow()
                    self.db.add(alert)

            await self.db.commit()

            self.logger.info("price_tracking_completed", triggered_count=len(triggered_alerts))

            # Queue notifications for triggered alerts
            await self._queue_notifications(triggered_alerts)

            return {
                "status": "completed",
                "alerts_checked": len(alerts),
                "alerts_triggered": len(triggered_alerts),
            }

        except Exception as e:
            self.logger.error("price_tracking_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    async def _should_trigger_alert(self, alert: PriceAlert, new_price: Decimal, pct_change: float) -> bool:
        """Determine if alert should be triggered."""
        if alert.alert_type == "below_price":
            return new_price < alert.target_price

        elif alert.alert_type == "percentage_drop":
            return pct_change < -alert.threshold_percentage

        elif alert.alert_type == "back_in_stock":
            # Fetch product availability
            product = await self.db.get(Product, alert.product_id)
            return product and product.availability == "in_stock"

        return False

    async def _queue_notifications(self, triggered_alerts: List[Dict[str, Any]]) -> None:
        """Queue notifications for triggered alerts."""
        for alert_info in triggered_alerts:
            # Create notification record
            notification = Notification(
                user_id=alert_info["user_id"],
                notification_type="price_drop",
                title=f"Price Alert Triggered!",
                message=f"Price dropped from ₹{float(alert_info['old_price']):,.0f} to ₹{float(alert_info['new_price']):,.0f} ({alert_info['pct_change']:.1f}%)",
                data={
                    "alert_id": str(alert_info["alert_id"]),
                    "product_id": str(alert_info["product_id"]),
                    "old_price": float(alert_info["old_price"]),
                    "new_price": float(alert_info["new_price"]),
                    "pct_change": alert_info["pct_change"],
                },
                is_read=False,
                sent_at=datetime.utcnow(),
            )
            self.db.add(notification)

        await self.db.commit()
        self.logger.info("notifications_queued", count=len(triggered_alerts))
