"""handlers package — re-exports all public builder functions."""
from handlers.product import build_add_product_handler, build_bulk_product_handler
from handlers.category import build_add_category_handler, list_categories
from handlers.auth import build_auth_handler, logout_command

__all__ = [
    "build_add_product_handler",
    "build_bulk_product_handler",
    "build_add_category_handler",
    "list_categories",
    "build_auth_handler",
    "logout_command",
]
