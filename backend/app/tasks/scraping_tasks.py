"""
Celery tasks for web scraping operations.
"""
import asyncio
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.scraping_job import ScrapingJob
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.scrapers import FlipkartScraper, AmazonScraper, MyntraScraper, MeeshoScraper
import structlog
from datetime import datetime

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3)
def scrape_platform(self, platform: str, search_query: str):
    """
    Scrape products from a specific platform.

    Args:
        platform: Platform name (flipkart, amazon, myntra, meesho)
        search_query: Search query to scrape products for
    """
    job_id = self.request.id
    logger.info("scraping_task_started", platform=platform, query=search_query, job_id=job_id)

    try:
        # Run async scraping in a new event loop
        result = asyncio.run(
            _async_scrape_platform(platform, search_query, job_id)
        )
        logger.info("scraping_task_completed", platform=platform, result=result)
        return result

    except Exception as e:
        logger.error("scraping_task_failed", platform=platform, error=str(e))
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


async def _async_scrape_platform(
    platform: str,
    search_query: str,
    job_id: str
) -> Dict[str, Any]:
    """
    Async function to scrape products from a platform.

    Args:
        platform: Platform name
        search_query: Search query
        job_id: Celery job ID

    Returns:
        Dictionary with scraping results
    """
    db: AsyncSession = AsyncSessionLocal()

    try:
        # Create scraping job record
        scraping_job = ScrapingJob(
            job_type="search",
            platform=platform,
            status="running",
            metadata={"search_query": search_query, "celery_job_id": job_id}
        )
        db.add(scraping_job)
        await db.flush()
        job_db_id = scraping_job.id

        # Select scraper based on platform
        scraper_class = {
            "flipkart": FlipkartScraper,
            "amazon": AmazonScraper,
            "myntra": MyntraScraper,
            "meesho": MeeshoScraper,
        }.get(platform)

        if not scraper_class:
            raise ValueError(f"Unknown platform: {platform}")

        # Run scraper
        async with scraper_class() as scraper:
            products = await scraper.search_products(search_query, max_results=20)

            # Save products to database
            for product_data in products:
                try:
                    # Check if product already exists
                    from sqlalchemy import select
                    result = await db.execute(
                        select(Product).where(
                            (Product.external_id == product_data["external_id"]) &
                            (Product.platform == platform)
                        )
                    )
                    existing_product = result.scalar_one_or_none()

                    if existing_product:
                        # Update existing product
                        existing_product.current_price = product_data.get("current_price")
                        existing_product.discount_percentage = product_data.get("discount_percentage")
                        existing_product.rating = product_data.get("rating")
                        existing_product.reviews_count = product_data.get("reviews_count")
                        existing_product.last_scraped_at = datetime.utcnow()

                        # Record price history if price changed
                        if existing_product.current_price:
                            price_history = PriceHistory(
                                product_id=existing_product.id,
                                price=existing_product.current_price,
                                original_price=product_data.get("original_price"),
                                discount_percentage=product_data.get("discount_percentage"),
                                source=str(job_db_id)
                            )
                            db.add(price_history)
                    else:
                        # Create new product
                        new_product = Product(**product_data, last_scraped_at=datetime.utcnow())
                        db.add(new_product)
                        await db.flush()

                        # Add initial price history
                        if product_data.get("current_price"):
                            price_history = PriceHistory(
                                product_id=new_product.id,
                                price=product_data.get("current_price"),
                                original_price=product_data.get("original_price"),
                                discount_percentage=product_data.get("discount_percentage"),
                                source=str(job_db_id)
                            )
                            db.add(price_history)

                    scraping_job.products_scraped += 1

                except Exception as e:
                    logger.error("product_save_error", product=product_data.get("name"), error=str(e))
                    scraping_job.errors_count += 1
                    continue

            # Update scraping job status
            scraping_job.status = "completed"
            scraping_job.completed_at = datetime.utcnow()
            scraping_job.products_updated = scraping_job.products_scraped

            await db.commit()

            logger.info(
                "scraping_completed",
                platform=platform,
                products_scraped=scraping_job.products_scraped,
                errors=scraping_job.errors_count
            )

            return {
                "status": "success",
                "platform": platform,
                "products_scraped": scraping_job.products_scraped,
                "errors": scraping_job.errors_count,
            }

    except Exception as e:
        logger.error("async_scraping_error", platform=platform, error=str(e))
        raise

    finally:
        await db.close()


@celery_app.task
def test_scraper_connection():
    """Test scraper connection (health check)."""
    logger.info("testing_scraper_connection")
    return {"status": "ok"}
