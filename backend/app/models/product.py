"""
Product model for storing e-commerce product data.
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, Integer, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.base import IDMixin, TimestampMixin


class Product(Base, IDMixin, TimestampMixin):
    """Product model for storing product information from various platforms."""

    __tablename__ = "products"

    # External identification
    external_id = Column(String(255), nullable=False)  # Platform-specific product ID
    platform = Column(String(50), nullable=False)  # flipkart, amazon, myntra, meesho

    # Product details
    name = Column(String(500), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    brand = Column(String(255))

    # Images and URLs
    image_url = Column(Text)
    product_url = Column(Text, nullable=False)

    # Pricing
    current_price = Column(Numeric(10, 2))
    original_price = Column(Numeric(10, 2))
    discount_percentage = Column(Numeric(5, 2))

    # Reviews and ratings
    rating = Column(Numeric(3, 2))  # 0.00 to 5.00
    reviews_count = Column(Integer)

    # Availability
    availability = Column(String(50))  # in_stock, out_of_stock, limited

    # Scraping metadata
    last_scraped_at = Column(DateTime)

    # Relationships
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    price_alerts = relationship("PriceAlert", back_populates="product", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("external_id", "platform", name="unique_product_platform"),
        Index("idx_products_category", "category"),
        Index("idx_products_platform", "platform"),
        Index("idx_products_brand", "brand"),
        Index("idx_products_name_fulltext", "name", postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"}),
    )

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, platform={self.platform}, price={self.current_price})>"
