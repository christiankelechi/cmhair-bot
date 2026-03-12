"""handlers/product package."""
from handlers.product.media_steps import ProductHandler
from telegram.ext import ConversationHandler


def build_add_product_handler() -> ConversationHandler:
    return ProductHandler().build()


__all__ = ["build_add_product_handler"]
