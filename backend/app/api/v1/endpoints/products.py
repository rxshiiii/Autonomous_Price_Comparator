"""
Product API endpoints for searching, filtering, and tracking products.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.product import Product
from app.services.product_service import ProductService
from app.schemas.product import (
    ProductResponse,
    ProductDetailResponse,
    PriceHistoryResponse,
    ProductSearchResponse,
    PriceComparisonItem,
)

router = APIRouter()


@router.get("/search", response_model=ProductSearchResponse)
async def search_products(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    platform: Optional[str] = Query(None, description="Filter by platform (flipkart, amazon, myntra, meesho)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    sort_by: str = Query("relevance", description="Sort by: relevance, price_low, price_high, rating, newest"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search for products across platforms with advanced filtering.

    Query Parameters:
    - **q**: Search query (required)
    - **category**: Filter by product category
    - **platform**: Filter by platform
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **min_rating**: Minimum rating (0-5)
    - **sort_by**: Sort order (relevance, price_low, price_high, rating, newest)
    - **limit**: Number of results (1-100)
    - **offset**: Pagination offset

    Returns:
    - **query**: The search query used
    - **total_results**: Total matching products
    - **products**: List of product results
    """
    products, total_count = await ProductService.search_products(
        db=db,
        query=q,
        category=category,
        platform=platform,
        min_price=Decimal(str(min_price)) if min_price else None,
        max_price=Decimal(str(max_price)) if max_price else None,
        min_rating=Decimal(str(min_rating)) if min_rating else None,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )

    return ProductSearchResponse(
        query=q,
        total_results=total_count,
        products=[ProductResponse.model_validate(p) for p in products],
    )


@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product_details(
    product_id: str,
    days: int = Query(30, ge=1, le=365, description="Days of price history to retrieve"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific product including price history.

    Path Parameters:
    - **product_id**: Product UUID

    Query Parameters:
    - **days**: Number of days of price history (1-365)

    Returns:
    - **product**: Product details
    - **price_history**: List of historical prices
    - **lowest_price**: Lowest price in the period
    - **highest_price**: Highest price in the period
    """
    product = await ProductService.get_product_by_id(db, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Get price history
    price_history = await ProductService.get_product_price_history(db, product_id, days=days)

    # Calculate min/max prices
    prices = [float(ph.price) for ph in price_history]
    lowest_price = Decimal(str(min(prices))) if prices else None
    highest_price = Decimal(str(max(prices))) if prices else None

    return ProductDetailResponse(
        product=ProductResponse.model_validate(product),
        price_history=[PriceHistoryResponse.model_validate(ph) for ph in price_history],
        lowest_price=lowest_price,
        highest_price=highest_price,
    )


@router.get("/compare/price-comparison")
async def compare_product_prices(
    query: str = Query(..., min_length=1, description="Product name to compare"),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare prices of the same product across different platforms.

    Query Parameters:
    - **query**: Product name to search for

    Returns:
    - Dictionary with platform names as keys
    - Each platform has:
      - **platform**: Platform name
      - **current_price**: Current price
      - **original_price**: Original price
      - **discount_percentage**: Discount percentage
      - **url**: Product URL
    """
    comparison_dict = await ProductService.get_price_comparison(
        db=db,
        product_name=query,
        platforms=["flipkart", "amazon", "myntra", "meesho"]
    )

    result = {}
    for platform, product in comparison_dict.items():
        result[platform] = PriceComparisonItem(
            platform=platform,
            current_price=product.current_price,
            original_price=product.original_price,
            discount_percentage=product.discount_percentage,
            url=product.product_url,
        )

    return result


@router.get("/trending")
async def get_trending_products(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get trending products based on ratings and reviews.

    Query Parameters:
    - **platform**: Optional platform filter
    - **limit**: Number of results (1-50)

    Returns:
    - List of trending product objects
    """
    products = await ProductService.get_trending_products(
        db=db,
        platform=platform,
        limit=limit
    )

    return [ProductResponse.model_validate(p) for p in products]


@router.post("/track")
async def track_product(
    product_id: str,
    notes: Optional[str] = Query(None, max_length=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a product to user's watchlist for price tracking.

    Path Parameters:
    - **product_id**: Product UUID to track

    Query Parameters:
    - **notes**: Optional notes about the product

    Returns:
    - Success message with tracked product ID
    """
    # Verify product exists
    product = await ProductService.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Track product
    tracked = await ProductService.track_product(
        db=db,
        user_id=str(current_user.id),
        product_id=product_id,
        notes=notes
    )

    return {
        "message": "Product added to watchlist",
        "product_id": str(tracked.product_id),
        "tracked_at": tracked.added_at,
    }


@router.delete("/track/{product_id}")
async def untrack_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a product from user's watchlist.

    Path Parameters:
    - **product_id**: Product UUID to untrack

    Returns:
    - Success message
    """
    success = await ProductService.untrack_product(
        db=db,
        user_id=str(current_user.id),
        product_id=product_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in watchlist"
        )

    return {"message": "Product removed from watchlist"}


@router.get("/tracked")
async def get_tracked_products(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all products tracked by the current user.

    Query Parameters:
    - **limit**: Number of results (1-100)
    - **offset**: Pagination offset

    Returns:
    - **total**: Total number of tracked products
    - **products**: List of tracked products
    - **limit**: Results limit
    - **offset**: Pagination offset
    """
    products, total_count = await ProductService.get_user_tracked_products(
        db=db,
        user_id=str(current_user.id),
        limit=limit,
        offset=offset
    )

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "products": [ProductResponse.model_validate(p) for p in products],
    }


@router.get("/category/{category}")
async def get_products_by_category(
    category: str,
    platform: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get products by category.

    Path Parameters:
    - **category**: Product category

    Query Parameters:
    - **platform**: Optional platform filter
    - **limit**: Number of results (1-100)

    Returns:
    - List of products in the category
    """
    products = await ProductService.get_products_by_category(
        db=db,
        category=category,
        platform=platform,
        limit=limit
    )

    return [ProductResponse.model_validate(p) for p in products]
