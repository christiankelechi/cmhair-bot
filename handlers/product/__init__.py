"""handlers/product package."""
from handlers.product.excel_handler import ExcelProductHandler
from handlers.product.single_handler import SingleProductHandler
from telegram.ext import ConversationHandler

def build_add_product_handler() -> ConversationHandler:
    return SingleProductHandler().build()

def build_bulk_product_handler() -> ConversationHandler:
    return ExcelProductHandler().build()

__all__ = ["build_add_product_handler", "build_bulk_product_handler"]
