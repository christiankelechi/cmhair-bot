"""Category handler — /categories and /addcategory."""
import logging
import api
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters,
)
from handlers.base import BaseHandler
from states import CAT_NAME, CAT_SLUG, CAT_DESCRIPTION, CAT_CONFIRM

log = logging.getLogger(__name__)


class CategoryHandler(BaseHandler):

    async def list_all(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.require_auth(update, ctx):
            return
        try:
            cats = await api.get_categories(self.token(ctx))
        except Exception as exc:
            await update.message.reply_text(f"❌ Could not load categories: {exc}")
            return
        if not cats:
            await update.message.reply_text("No categories. Use /addcategory to create one.")
            return
        lines = ["📂 *Product Categories*\n"] + [f"• *{c['name']}* — `{c['slug']}`" for c in cats]
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        if not await self.require_auth(update, ctx):
            return ConversationHandler.END
        await update.message.reply_text("📂 *Add Category*\n\nName?", parse_mode="Markdown")
        return CAT_NAME

    async def ask_slug(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        ctx.user_data["cat_name"] = update.message.text.strip()
        hint = self.slugify(ctx.user_data["cat_name"], max_len=60)
        ctx.user_data["_cat_slug"] = hint
        await update.message.reply_text(f"Slug: `{hint}`\n\nSend custom slug or /use\\_suggested", parse_mode="Markdown")
        return CAT_SLUG

    async def ask_description(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text.strip()
        ctx.user_data["cat_slug"] = ctx.user_data["_cat_slug"] if text == "/use_suggested" else self.slugify(text, 60)
        await update.message.reply_text(f"Slug: `{ctx.user_data['cat_slug']}`\n\nDescription? — or /skip", parse_mode="Markdown")
        return CAT_DESCRIPTION

    async def confirm_prompt(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text.strip()
        if text != "/skip":
            ctx.user_data["cat_desc"] = text
        d = ctx.user_data
        body = f"📂 *{d['cat_name']}*\nSlug: `{d['cat_slug']}`"
        if d.get("cat_desc"):
            body += f"\nDesc: {d['cat_desc']}"
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Create", callback_data="catconfirm:yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="catconfirm:no"),
        ]])
        await update.message.reply_text(body + "\n\nConfirm?", parse_mode="Markdown", reply_markup=kb)
        return CAT_CONFIRM

    async def receive_confirm(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        if query.data == "catconfirm:no":
            await query.edit_message_text("❌ Cancelled.")
            return ConversationHandler.END
        d = ctx.user_data
        payload = {"name": d["cat_name"], "slug": d["cat_slug"], "is_active": True, "sort_order": 0}
        if d.get("cat_desc"):
            payload["description"] = d["cat_desc"]
        await query.edit_message_text("⏳ Creating…")
        try:
            result = await api.create_category(payload, self.token(ctx))
            await ctx.bot.send_message(query.message.chat_id, f"🎉 Category *{result['name']}* created! Slug: `{result['slug']}`", parse_mode="Markdown")
        except Exception as exc:
            await ctx.bot.send_message(query.message.chat_id, f"❌ Failed: `{exc}`", parse_mode="Markdown")
        return ConversationHandler.END

    async def cancel(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("❌ Cancelled.")
        return ConversationHandler.END

    def build_add_handler(self) -> ConversationHandler:
        txt = filters.TEXT & ~filters.COMMAND
        return ConversationHandler(
            entry_points=[CommandHandler("addcategory", self.start)],
            states={
                CAT_NAME:        [MessageHandler(txt, self.ask_slug)],
                CAT_SLUG:        [MessageHandler(txt, self.ask_description), CommandHandler("use_suggested", self.ask_description)],
                CAT_DESCRIPTION: [MessageHandler(txt, self.confirm_prompt), CommandHandler("skip", self.confirm_prompt)],
                CAT_CONFIRM:     [CallbackQueryHandler(self.receive_confirm, pattern=r"^catconfirm:")],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
        )
