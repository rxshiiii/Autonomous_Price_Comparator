"""
Utility functions for AI agents.
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
import structlog


logger = structlog.get_logger()


def format_user_profile(user: Any) -> str:
    """Format user profile for GROQ prompt."""
    interests = getattr(user, "interests", [])
    age = getattr(user, "age", "Unknown")

    interests_str = ", ".join(interests) if isinstance(interests, list) else str(interests)

    return f"""
User Profile:
- Age: {age}
- Interests: {interests_str}
"""


def format_product_for_scoring(product: Any) -> Dict[str, Any]:
    """Extract and format product data for scoring."""
    return {
        "name": product.name,
        "category": product.category or "Uncategorized",
        "price": f"₹{float(product.current_price):,.0f}" if product.current_price else "N/A",
        "rating": f"{float(product.rating):.1f}/5" if product.rating else "N/A",
        "reviews": product.reviews_count or 0,
        "brand": product.brand or "Unknown",
        "platform": product.platform,
    }


def format_product_list_for_prompt(products: List[Any]) -> str:
    """Format list of products for inclusion in prompt."""
    if not products:
        return "No products available"

    formatted = []
    for i, product in enumerate(products[:10], 1):  # Limit to 10 products per prompt
        product_data = format_product_for_scoring(product)
        formatted.append(f"""
Product {i}:
- Name: {product_data['name']}
- Category: {product_data['category']}
- Price: {product_data['price']}
- Rating: {product_data['rating']}
- Reviews: {product_data['reviews']}
- Brand: {product_data['brand']}
""")

    return "\n".join(formatted)


def parse_groq_json_scores(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse GROQ JSON response containing product scores."""
    try:
        if isinstance(response, dict):
            # Check if it's a single score or a list of scores
            if "scores" in response:
                return response["scores"]
            elif "products" in response:
                return response["products"]
            elif "score" in response:
                # Single productresponse
                return [response]
            else:
                logger.warning("unexpected_groq_response_format", response=response)
                return []

        return []
    except Exception as e:
        logger.error("error_parsing_groq_scores", error=str(e))
        return []


def calculate_price_percentage_change(old_price: Decimal, new_price: Decimal) -> float:
    """
    Calculate percentage change in price.

    Returns:
        Negative value for price decrease, positive for increase
    """
    if old_price == 0:
        return 0

    change = ((new_price - old_price) / old_price) * 100
    return round(float(change), 2)


def is_within_quiet_hours(
    notification_start: Any,
    notification_end: Any,
    current_time: Any = None
) -> bool:
    """
    Check if current time is within quiet hours.

    Args:
        notification_start: Start time (HH:MM format)
        notification_end: End time (HH:MM format)
        current_time: Current time (defaults to datetime.time.now())

    Returns:
        True if within quiet hours, False otherwise
    """
    if current_time is None:
        from datetime import datetime
        current_time = datetime.utcnow().time()

    start_time = notification_start if not isinstance(notification_start, str) else type(current_time).fromisoformat(notification_start)
    end_time = notification_end if not isinstance(notification_end, str) else type(current_time).fromisoformat(notification_end)

    # Handle wrap-around (e.g., 22:00 to 09:00)
    if start_time <= end_time:
        return start_time <= current_time <= end_time
    else:
        return current_time >= start_time or current_time <= end_time


def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Batch a list of items into chunks."""
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
