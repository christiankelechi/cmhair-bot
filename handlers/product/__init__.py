"""handlers/product package."""
from handlers.product.excel_handler import ExcelProductHandler
from telegram.ext import ConversationHandler

def build_add_product_handler() -> ConversationHandler:
    return ExcelProductHandler().build()

__all__ = ["build_add_product_handler"]
