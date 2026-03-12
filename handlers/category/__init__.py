"""handlers/category package."""
from handlers.category.handler import CategoryHandler
from telegram.ext import ConversationHandler

_h = CategoryHandler()
list_categories = _h.list_all


def build_add_category_handler() -> ConversationHandler:
    return _h.build_add_handler()


__all__ = ["list_categories", "build_add_category_handler"]
