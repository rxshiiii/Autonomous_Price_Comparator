"""
Onboarding service for user preference collection and setup.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, UserPreference
from app.models.onboarding import OnboardingProgress
from app.models.product import Product
from app.models.recommendation import Recommendation
from app.db.session import AsyncSessionLocal


logger = logging.getLogger(__name__)


class OnboardingService:
    """Service for managing user onboarding flow and preference setup."""

    # Onboarding steps
    STEPS = {
        'welcome': {
            'order': 1,
            'name': 'Welcome',
            'required': True
        },
        'preferences': {
            'order': 2,
            'name': 'Preferences',
            'required': True
        },
        'budget': {
            'order': 3,
            'name': 'Budget',
            'required': False
        },
        'products': {
            'order': 4,
            'name': 'Initial Products',
            'required': True
        },
        'notifications': {
            'order': 5,
            'name': 'Notifications',
            'required': True
        },
        'complete': {
            'order': 6,
            'name': 'Complete',
            'required': True
        }
    }

    # Product categories for preference selection
    CATEGORIES = [
        {
            'id': 'electronics',
            'name': 'Electronics',
            'icon': '📱',
            'description': 'Phones, laptops, accessories'
        },
        {
            'id': 'fashion',
            'name': 'Fashion',
            'icon': '👕',
            'description': 'Clothing, shoes, accessories'
        },
        {
            'id': 'home',
            'name': 'Home & Kitchen',
            'icon': '🏠',
            'description': 'Kitchen appliances, furniture'
        },
        {
            'id': 'sports',
            'name': 'Sports & Outdoor',
            'icon': '⚽',
            'description': 'Sports equipment, outdoor gear'
        },
        {
            'id': 'beauty',
            'name': 'Beauty & Personal Care',
            'icon': '💄',
            'description': 'Skincare, cosmetics, health products'
        },
        {
            'id': 'books',
            'name': 'Books & Media',
            'icon': '📚',
            'description': 'Books, movies, music'
        }
    ]

    async def get_onboarding_progress(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Dict[str, any]:
        """Get user's onboarding progress."""
        try:
            from sqlalchemy import select

            # Get onboarding progress record
            result = await db.execute(
                select(OnboardingProgress).filter(OnboardingProgress.user_id == user_id)
            )
            progress = result.scalar_one_or_none()

            if not progress:
                # Create new progress record for new users
                progress = OnboardingProgress(
                    user_id=user_id,
                    current_step='welcome',
                    completed_steps=[],
                    is_completed=False
                )
                db.add(progress)
                await db.commit()

            return {
                'user_id': str(progress.user_id),
                'current_step': progress.current_step,
                'completed_steps': progress.completed_steps,
                'is_completed': progress.is_completed,
                'steps': self.STEPS,
                'progress_percentage': self._calculate_progress(progress.completed_steps),
                'last_updated': progress.updated_at.isoformat() if progress.updated_at else None
            }

        except Exception as e:
            logger.error(f"Failed to get onboarding progress: {e}")
            raise

    async def complete_onboarding_step(
        self,
        db: AsyncSession,
        user_id: UUID,
        step: str,
        data: Dict = None
    ) -> Dict[str, any]:
        """Mark an onboarding step as complete."""
        try:
            from sqlalchemy import select

            # Validate step exists
            if step not in self.STEPS:
                raise ValueError(f"Invalid onboarding step: {step}")

            # Get progress record
            result = await db.execute(
                select(OnboardingProgress).filter(OnboardingProgress.user_id == user_id)
            )
            progress = result.scalar_one_or_none()

            if not progress:
                raise ValueError("User onboarding not initialized")

            # Mark step as complete
            if step not in progress.completed_steps:
                progress.completed_steps.append(step)

            # Process step-specific data
            if data:
                await self._process_step_data(db, user_id, step, data)

            # Update current step to next
            current_order = self.STEPS[step]['order']
            next_steps = [
                (s_name, s_info) for s_name, s_info in self.STEPS.items()
                if s_info['order'] > current_order
            ]

            if next_steps:
                progress.current_step = next_steps[0][0]
            else:
                progress.current_step = 'complete'
                progress.is_completed = True

            progress.updated_at = datetime.utcnow()

            await db.commit()

            logger.info(f"Completed onboarding step '{step}' for user {user_id}")

            return await self.get_onboarding_progress(db, user_id)

        except Exception as e:
            logger.error(f"Failed to complete onboarding step: {e}")
            await db.rollback()
            raise

    async def _process_step_data(
        self,
        db: AsyncSession,
        user_id: UUID,
        step: str,
        data: Dict
    ) -> None:
        """Process and store data from each onboarding step."""
        try:
            if step == 'preferences':
                await self._save_user_preferences(db, user_id, data)

            elif step == 'budget':
                await self._save_budget_preferences(db, user_id, data)

            elif step == 'products':
                await self._save_initial_products(db, user_id, data)

            elif step == 'notifications':
                await self._save_notification_preferences(db, user_id, data)

        except Exception as e:
            logger.error(f"Failed to process step data for {step}: {e}")
            raise

    async def _save_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        data: Dict
    ) -> None:
        """Save user category and interest preferences."""
        try:
            categories = data.get('categories', [])
            interests = data.get('interests', [])

            # Clear existing preferences
            await db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).delete()

            # Add new preferences
            for category in categories:
                preference = UserPreference(
                    user_id=user_id,
                    category=category,
                    interest='general',
                    priority=3
                )
                db.add(preference)

            for interest in interests:
                # Extract category from interest format "category:interest"
                if ':' in interest:
                    category, interest_name = interest.split(':', 1)
                    preference = UserPreference(
                        user_id=user_id,
                        category=category,
                        interest=interest_name,
                        priority=5  # Higher priority for specific interests
                    )
                    db.add(preference)

            await db.commit()

        except Exception as e:
            logger.error(f"Failed to save user preferences: {e}")
            await db.rollback()
            raise

    async def _save_budget_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        data: Dict
    ) -> None:
        """Save budget preferences per category."""
        try:
            budget_ranges = data.get('budget_ranges', {})

            # Update preferences with budget metadata
            for category, budget_range in budget_ranges.items():
                preferences = await db.query(UserPreference).filter(
                    UserPreference.user_id == user_id,
                    UserPreference.category == category
                ).all()

                for pref in preferences:
                    if not pref.metadata:
                        pref.metadata = {}
                    pref.metadata['budget_min'] = budget_range.get('min')
                    pref.metadata['budget_max'] = budget_range.get('max')

            await db.commit()

        except Exception as e:
            logger.error(f"Failed to save budget preferences: {e}")
            await db.rollback()

    async def _save_initial_products(
        self,
        db: AsyncSession,
        user_id: UUID,
        data: Dict
    ) -> None:
        """Track initial products selected by user to seed recommendations."""
        try:
            from app.models.user import UserTrackedProduct

            product_ids = data.get('product_ids', [])

            for product_id in product_ids:
                # Check if product exists
                existing = await db.query(UserTrackedProduct).filter(
                    UserTrackedProduct.user_id == user_id,
                    UserTrackedProduct.product_id == product_id
                ).first()

                if not existing:
                    tracked = UserTrackedProduct(
                        user_id=user_id,
                        product_id=product_id,
                        notes='Added during onboarding'
                    )
                    db.add(tracked)

            await db.commit()

        except Exception as e:
            logger.error(f"Failed to save initial products: {e}")
            await db.rollback()

    async def _save_notification_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        data: Dict
    ) -> None:
        """Save notification preferences."""
        try:
            from app.models.notification import UserNotificationPreferences

            # Get or create notification preferences
            prefs = await db.query(UserNotificationPreferences).filter(
                UserNotificationPreferences.user_id == user_id
            ).one_or_none()

            if not prefs:
                prefs = UserNotificationPreferences(user_id=user_id)
                db.add(prefs)

            # Update preferences
            prefs.websocket_enabled = data.get('websocket_enabled', True)
            prefs.email_enabled = data.get('email_enabled', True)
            prefs.max_notifications_per_day = data.get('max_notifications_per_day', 5)
            prefs.price_drop_threshold_percentage = data.get('price_drop_threshold', 10)

            # Parse quiet hours
            if 'quiet_hours' in data:
                prefs.notification_quiet_hours_start = data['quiet_hours']['start']
                prefs.notification_quiet_hours_end = data['quiet_hours']['end']

            await db.commit()

        except Exception as e:
            logger.error(f"Failed to save notification preferences: {e}")
            await db.rollback()

    async def get_category_suggestions(self) -> List[Dict]:
        """Get available product categories for onboarding."""
        return self.CATEGORIES

    async def get_popular_products_by_category(
        self,
        db: AsyncSession,
        category: str,
        limit: int = 12
    ) -> List[Dict]:
        """Get popular products in a category for onboarding selection."""
        try:
            from sqlalchemy import select, desc

            # Get popular products (sorted by rating/reviews)
            query = select(Product).where(
                Product.category == category,
                Product.current_price.isnot(None),
                Product.rating.isnot(None)
            ).order_by(
                desc(Product.rating),
                desc(Product.reviews_count)
            ).limit(limit)

            result = await db.execute(query)
            products = result.scalars().all()

            return [
                {
                    'id': str(product.id),
                    'name': product.name,
                    'image_url': product.image_url,
                    'current_price': float(product.current_price),
                    'rating': float(product.rating) if product.rating else None,
                    'reviews_count': product.reviews_count,
                    'platform': product.platform,
                    'category': product.category
                }
                for product in products
            ]

        except Exception as e:
            logger.error(f"Failed to get popular products: {e}")
            return []

    async def seed_initial_recommendations(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> bool:
        """Generate initial recommendations based on onboarding selections."""
        try:
            # This would trigger the recommendation agent
            # For now, just mark that recommendations should be generated
            logger.info(f"Seeding initial recommendations for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to seed recommendations: {e}")
            return False

    def _calculate_progress(self, completed_steps: List[str]) -> int:
        """Calculate onboarding progress percentage."""
        total_steps = len(self.STEPS)
        if total_steps == 0:
            return 0
        return int((len(completed_steps) / total_steps) * 100)

    async def skip_onboarding(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Dict[str, any]:
        """Allow user to skip onboarding."""
        try:
            from sqlalchemy import select

            result = await db.execute(
                select(OnboardingProgress).filter(OnboardingProgress.user_id == user_id)
            )
            progress = result.scalar_one_or_none()

            if progress:
                progress.is_completed = True
                progress.current_step = 'complete'
                progress.updated_at = datetime.utcnow()
                await db.commit()

            logger.info(f"User {user_id} skipped onboarding")
            return await self.get_onboarding_progress(db, user_id)

        except Exception as e:
            logger.error(f"Failed to skip onboarding: {e}")
            raise


# Global service instance
onboarding_service = OnboardingService()


async def get_onboarding_service() -> OnboardingService:
    """Dependency function to get onboarding service instance."""
    return onboarding_service