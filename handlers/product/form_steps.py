"""Steps 1–8: name → slug → price → stock → description → category → badge."""
import logging
import api
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from handlers.base import BaseHandler
from states import (
    ASK_NAME, ASK_SLUG, ASK_PRICE, ASK_ORIGINAL_PRICE, ASK_STOCK,
    ASK_DESCRIPTION, ASK_CATEGORY, ASK_BADGE, ASK_COLORS,
)

log = logging.getLogger(__name__)
BADGES = ["new", "sale", "bestseller", "limited", "none"]


class FormSteps(BaseHandler):

    async def start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        if not await self.require_auth(update, ctx):
            return ConversationHandler.END
        ctx.user_data.setdefault("images", [])
        # preserve token/user info but clear product draft
        tok = ctx.user_data.get("token")
        name = ctx.user_data.get("user_name")
        ctx.user_data.clear()
        ctx.user_data["token"] = tok
        ctx.user_data["user_name"] = name
        ctx.user_data["images"] = []
        await update.message.reply_text("🛍️ *Add New Product*\n\nStep 1 — *Product name*?", parse_mode="Markdown")
        return ASK_NAME

    async def ask_slug(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        ctx.user_data["name"] = update.message.text.strip()
        hint = self.slugify(ctx.user_data["name"])
        ctx.user_data["_slug_hint"] = hint
        await update.message.reply_text(
            f"Step 2 — *Slug*\nSuggested: `{hint}`\n\nSend custom slug or /use\\_suggested",
            parse_mode="Markdown",
        )
        return ASK_SLUG

    async def ask_price(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text.strip()
        slug = ctx.user_data["_slug_hint"] if text == "/use_suggested" else self.slugify(text)
        ctx.user_data["slug"] = slug
        await update.message.reply_text(f"✅ Slug: `{slug}`\n\nStep 3 — *Price* ($)?", parse_mode="Markdown")
        return ASK_PRICE

    async def ask_original_price(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            ctx.user_data["price"] = float(update.message.text.strip().replace(",", ""))
        except ValueError:
            await update.message.reply_text("❌ Enter a valid number e.g. 15000")
            return ASK_PRICE
        await update.message.reply_text("Step 4 — *Original price* ($)? — or /skip", parse_mode="Markdown")
        return ASK_ORIGINAL_PRICE

    async def ask_stock(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text.strip()
        if text != "/skip":
            try:
                ctx.user_data["original_price"] = float(text.replace(",", ""))
            except ValueError:
                await update.message.reply_text("❌ Invalid. Try again or /skip")
                return ASK_ORIGINAL_PRICE
        await update.message.reply_text("Step 5 — *Stock quantity*?", parse_mode="Markdown")
        return ASK_STOCK

    async def ask_description(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            ctx.user_data["stock"] = int(update.message.text.strip())
        except ValueError:
            await update.message.reply_text("❌ Enter a whole number e.g. 50")
            return ASK_STOCK
        await update.message.reply_text("Step 6 — *Description*? — or /skip", parse_mode="Markdown")
        return ASK_DESCRIPTION

    async def ask_category(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text.strip()
        if text != "/skip":
            ctx.user_data["description"] = text
        try:
            cats = await api.get_categories(self.token(ctx))
        except Exception:
            cats = []
        ctx.user_data["_cats"] = {c["id"]: c["name"] for c in cats}
        if cats:
            kb = [[InlineKeyboardButton(c["name"], callback_data=f"cat:{c['id']}")] for c in cats]
            kb.append([InlineKeyboardButton("⏭ None", callback_data="cat:none")])
            await update.message.reply_text("Step 7 — *Category*?", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
            return ASK_CATEGORY
        return await self._ask_badge(update.message.chat_id, ctx)

    async def receive_category(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        val = query.data.split(":", 1)[1]
        if val != "none":
            ctx.user_data["category_id"] = val
            ctx.user_data["_category_name"] = ctx.user_data.get("_cats", {}).get(val, val)
        await query.edit_message_text("✅ Category set.")
        return await self._ask_badge(query.message.chat_id, ctx)

    async def _ask_badge(self, chat_id: int, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        kb = [[InlineKeyboardButton(b.title(), callback_data=f"badge:{b}")] for b in BADGES]
        await ctx.bot.send_message(chat_id=chat_id, text="Step 8 — *Badge*?", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return ASK_BADGE

    async def receive_badge(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        badge = query.data.split(":", 1)[1]
        ctx.user_data["badge"] = None if badge == "none" else badge
        await query.edit_message_text(f"✅ Badge: {badge}\n\nStep 9 — *Colors*? (comma-separated) — or /skip", parse_mode="Markdown")
        return ASK_COLORS
