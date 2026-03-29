"""
API v1 router - combines all endpoint routers.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, products, price_alerts

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Include product routes
api_router.include_router(products.router, prefix="/products", tags=["Products"])

# Include price alert routes
api_router.include_router(price_alerts.router, prefix="/price-alerts", tags=["Price Alerts"])

# Additional routers will be added here as we implement them:
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(products.router, prefix="/products", tags=["Products"])
# api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
# api_router.include_router(price_tracking.router, prefix="/price-alerts", tags=["Price Alerts"])
# api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
