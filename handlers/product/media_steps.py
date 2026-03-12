"""Steps 9–13 + build(): colors → lengths → bundles → cap_sizes → images → confirm."""
import logging
from typing import Any
import api
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters,
)
from handlers.product.form_steps import FormSteps
from states import (
    ASK_NAME, ASK_SLUG, ASK_PRICE, ASK_ORIGINAL_PRICE, ASK_STOCK,
    ASK_DESCRIPTION, ASK_CATEGORY, ASK_BADGE, ASK_COLORS,
    ASK_LENGTHS, ASK_BUNDLES, ASK_CAP_SIZES, ASK_IMAGES, ASK_CONFIRM,
)

log = logging.getLogger(__name__)


class ProductHandler(FormSteps):
    MAX_IMAGES = 10

    async def ask_lengths(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        if update.message.text.strip() != "/skip":
            ctx.user_data["colors"] = self.split_csv(update.message.text)
        await update.message.reply_text("Step 10 — *Lengths*? (e.g. 10inch) — or /skip", parse_mode="Markdown")
        return ASK_LENGTHS

    async def ask_bundles(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        if update.message.text.strip() != "/skip":
            ctx.user_data["lengths"] = self.split_csv(update.message.text)
        await update.message.reply_text("Step 11 — *Bundles*? (e.g. 1 Bundle) — or /skip", parse_mode="Markdown")
        return ASK_BUNDLES

    async def ask_cap_sizes(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        if update.message.text.strip() != "/skip":
            ctx.user_data["bundles"] = self.split_csv(update.message.text)
        await update.message.reply_text("Step 12 — *Cap sizes*? (e.g. Small, Medium) — or /skip", parse_mode="Markdown")
        return ASK_CAP_SIZES

    async def ask_images(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        if update.message.text.strip() != "/skip":
            ctx.user_data["cap_sizes"] = self.split_csv(update.message.text)
        await update.message.reply_text(
            "📸 *Step 13 — Upload images*\n\nSend photos one by one (max 10).\nSend /done when finished.",
            parse_mode="Markdown",
        )
        return ASK_IMAGES

    async def receive_image(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        images: list = ctx.user_data.setdefault("images", [])
        if len(images) >= self.MAX_IMAGES:
            await update.message.reply_text("⚠️ Max 10 images. Send /done to continue.")
            return ASK_IMAGES
        msg = await update.message.reply_text("⏳ Uploading…")
        try:
            photo = update.message.photo[-1]
            raw = await (await ctx.bot.get_file(photo.file_id)).download_as_bytearray()
            url = await api.upload_image(bytes(raw), self.token(ctx), f"product_{len(images)+1}.jpg")
            images.append(url)
            await msg.edit_text(f"✅ Image {len(images)} uploaded! Send more or /done.")
        except Exception as exc:
            log.error("Image upload failed: %s", exc)
            await msg.edit_text(f"❌ Upload failed: {exc}\nTry again or /done.")
        return ASK_IMAGES

    async def confirm_prompt(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Confirm & Create", callback_data="confirm:yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="confirm:no"),
        ]])
        await update.message.reply_text(
            self.summary(ctx.user_data) + "\n\n*Create this product?*",
            parse_mode="Markdown", reply_markup=kb,
        )
        return ASK_CONFIRM

    async def receive_confirm(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        if query.data == "confirm:no":
            await query.edit_message_text("❌ Cancelled.")
            return ConversationHandler.END
        d = ctx.user_data
        payload: dict[str, Any] = {
            "name": d["name"], "slug": d["slug"], "price": d["price"],
            "stock": d.get("stock", 0), "is_active": True, "is_archived": False, "is_muted": False,
        }
        for key in ("original_price", "description", "category_id", "badge", "colors", "lengths", "bundles", "cap_sizes"):
            if d.get(key):
                payload[key] = d[key]
        if d.get("images"):
            payload["images"] = d["images"]
        await query.edit_message_text("⏳ Creating product…")
        try:
            p = await api.create_product(payload, self.token(ctx))
            slug = p.get("slug", "")
            await ctx.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"🎉 *Product created!*\n\n• Name: {p.get('name')}\n• Slug: `{slug}`\n• Price: ₦{p.get('price'):,.0f}\n\n🔗 https://cmhairbyhills.org/product/{slug}",
                parse_mode="Markdown",
            )
        except Exception as exc:
            log.error("Product creation failed: %s", exc)
            await ctx.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Failed: `{exc}`", parse_mode="Markdown")
        return ConversationHandler.END

    async def cancel(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("❌ Cancelled. Use /addproduct to start again.")
        return ConversationHandler.END

    def build(self) -> ConversationHandler:
        txt = filters.TEXT & ~filters.COMMAND
        return ConversationHandler(
            entry_points=[CommandHandler("addproduct", self.start)],
            states={
                ASK_NAME:           [MessageHandler(txt, self.ask_slug)],
                ASK_SLUG:           [MessageHandler(txt, self.ask_price), CommandHandler("use_suggested", self.ask_price)],
                ASK_PRICE:          [MessageHandler(txt, self.ask_original_price)],
                ASK_ORIGINAL_PRICE: [MessageHandler(txt, self.ask_stock), CommandHandler("skip", self.ask_stock)],
                ASK_STOCK:          [MessageHandler(txt, self.ask_description)],
                ASK_DESCRIPTION:    [MessageHandler(txt, self.ask_category), CommandHandler("skip", self.ask_category)],
                ASK_CATEGORY:       [CallbackQueryHandler(self.receive_category, pattern=r"^cat:")],
                ASK_BADGE:          [CallbackQueryHandler(self.receive_badge, pattern=r"^badge:")],
                ASK_COLORS:         [MessageHandler(txt, self.ask_lengths), CommandHandler("skip", self.ask_lengths)],
                ASK_LENGTHS:        [MessageHandler(txt, self.ask_bundles), CommandHandler("skip", self.ask_bundles)],
                ASK_BUNDLES:        [MessageHandler(txt, self.ask_cap_sizes), CommandHandler("skip", self.ask_cap_sizes)],
                ASK_CAP_SIZES:      [MessageHandler(txt, self.ask_images), CommandHandler("skip", self.ask_images)],
                ASK_IMAGES:         [MessageHandler(filters.PHOTO, self.receive_image), CommandHandler("done", self.confirm_prompt)],
                ASK_CONFIRM:        [CallbackQueryHandler(self.receive_confirm, pattern=r"^confirm:")],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
        )
