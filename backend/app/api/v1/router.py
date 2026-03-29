"""
API v1 router - combines all endpoint routers.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, products, price_alerts, websockets

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Include product routes
api_router.include_router(products.router, prefix="/products", tags=["Products"])

# Include price alert routes
api_router.include_router(price_alerts.router, prefix="/price-alerts", tags=["Price Alerts"])

# Include WebSocket routes (Phase 5)
api_router.include_router(websockets.router, prefix="/ws", tags=["WebSockets"])

# Additional routers will be added here as we implement them:
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
# api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
