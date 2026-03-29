"""
Product Pydantic schemas for API requests and responses.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from decimal import Decimal


class ProductCreate(BaseModel):
    """Product creation schema."""
    external_id: str
    platform: str  # flipkart, amazon, myntra, meesho
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    product_url: str
    current_price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = None
    rating: Optional[Decimal] = None
    reviews_count: Optional[int] = None
    availability: str = "in_stock"


class ProductResponse(BaseModel):
    """Product response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_id: str
    platform: str
    name: str
    description: Optional[str]
    category: Optional[str]
    brand: Optional[str]
    image_url: Optional[str]
    product_url: str
    current_price: Optional[Decimal]
    original_price: Optional[Decimal]
    discount_percentage: Optional[Decimal]
    rating: Optional[Decimal]
    reviews_count: Optional[int]
    availability: str
    last_scraped_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class PriceHistoryResponse(BaseModel):
    """Price history response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    price: Decimal
    original_price: Optional[Decimal]
    discount_percentage: Optional[Decimal]
    recorded_at: datetime


class ProductDetailResponse(BaseModel):
    """Product detail response with price history."""
    model_config = ConfigDict(from_attributes=True)

    product: ProductResponse
    price_history: List[PriceHistoryResponse]
    lowest_price: Optional[Decimal]
    highest_price: Optional[Decimal]


class PriceComparisonItem(BaseModel):
    """Single item in price comparison."""
    model_config = ConfigDict(from_attributes=True)

    platform: str
    current_price: Optional[Decimal]
    original_price: Optional[Decimal]
    discount_percentage: Optional[Decimal]
    url: str


class ProductSearchResponse(BaseModel):
    """Product search response schema."""
    query: str
    total_results: int
    products: List[ProductResponse]


class ScrapingJobResponse(BaseModel):
    """Scraping job response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_type: str
    platform: str
    status: str
    products_scraped: int
    products_updated: int
    errors_count: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
