"""API v1 Router Aggregation.

Single entry point for all /api/v1 routes.
Each module registers its own routers with internal prefixes.
"""

from fastapi import APIRouter

# Public + Admin routers (separate for authz separation)
from app.modules.products.router import public_router as products_public_router
from app.modules.products.router import admin_router as products_admin_router

from app.modules.orders.router import router as orders_router
from app.modules.orders.router import admin_router as orders_admin_router

from app.modules.payments.router import router as payments_router

from app.modules.community.router import router as community_router

from app.modules.auth.router import router as auth_router

from app.modules.users.router import router as users_router

from app.modules.stores.router import router as stores_router

from app.modules.cart.router import router as cart_router

from app.modules.pricing.router import router as pricing_router

from app.modules.inventory.router import public_router as inventory_public_router
from app.modules.inventory.router import admin_router as inventory_admin_router

from app.modules.categories.router import public_router as categories_public_router
from app.modules.categories.router import admin_router as categories_admin_router

from app.modules.admin.router import router as admin_router

from app.modules.health.router import router as health_router


api_v1_router = APIRouter()

# Core commerce
api_v1_router.include_router(products_public_router)
api_v1_router.include_router(products_admin_router)

api_v1_router.include_router(orders_router)
api_v1_router.include_router(orders_admin_router)

api_v1_router.include_router(payments_router)

api_v1_router.include_router(cart_router)

# Catalog & Inventory
api_v1_router.include_router(stores_router)

api_v1_router.include_router(categories_public_router)
api_v1_router.include_router(categories_admin_router)

api_v1_router.include_router(inventory_public_router)
api_v1_router.include_router(inventory_admin_router)

api_v1_router.include_router(pricing_router)

# Users & Auth
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)

# Community
api_v1_router.include_router(community_router)

# Admin (cross-cutting)
api_v1_router.include_router(admin_router)

# Health (also registered at root level in main.py for backward compatibility)
api_v1_router.include_router(health_router)