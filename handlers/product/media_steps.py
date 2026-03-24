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
from utils.parser import parse_template, get_template_example

log = logging.getLogger(__name__)


class ProductHandler(FormSteps):
    MAX_IMAGES = 10

    async def start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        if not await self.require_auth(update, ctx):
            return ConversationHandler.END
        
        # Preserve auth/user info but clear previous product draft
        tok = ctx.user_data.get("token")
        name = ctx.user_data.get("user_name")
        roles = ctx.user_data.get("roles")
        ctx.user_data.clear()
        ctx.user_data["token"] = tok
        ctx.user_data["user_name"] = name
        ctx.user_data["roles"] = roles
        ctx.user_data["images"] = []

        await update.message.reply_text(
            "🛍️ *Add New Product*\n\n"
            "Please send a **Photo with a Caption** or a **Text Template** containing the product details.\n\n"
            "💡 *Tip:* Use /template to see the required format.\n"
            "*(Or just send the product name to start step-by-step)*",
            parse_mode="Markdown"
        )
        return ASK_NAME

    async def show_template_example(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "📋 *Product Template*\n\n"
            "Copy and fill this. You can send it as a text message or as a caption to a photo.\n\n"
            f"```\n{get_template_example()}\n```",
            parse_mode="Markdown"
        )

    async def handle_template_or_name(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.caption or update.message.text
        if not text:
            return ASK_NAME
        
        # Check if it looks like a template (has at least 3 colons)
        if text.count(':') >= 3:
            data = parse_template(text)
            if data.get('name') and data.get('price'):
                ctx.user_data.update(data)
                if not ctx.user_data.get('slug'):
                    ctx.user_data['slug'] = self.slugify(data['name'], data.get('product_name'))
                
                # Handle images if present
                if update.message.photo:
                    msg = await update.message.reply_text("⏳ Uploading image from template…")
                    try:
                        photo = update.message.photo[-1]
                        raw = await (await ctx.bot.get_file(photo.file_id)).download_as_bytearray()
                        url = await api.upload_image(bytes(raw), self.token(ctx), "template_image.jpg")
                        ctx.user_data.setdefault("images", []).append(url)
                        await msg.edit_text("✅ Image uploaded!")
                    except Exception as exc:
                        log.error("Template image upload failed: %s", exc)
                        await msg.edit_text(f"⚠️ Image upload failed: {exc}")

                # Try to find category ID if category name is provided
                if data.get('category_name'):
                    try:
                        cats = await api.get_categories(self.token(ctx))
                        for c in cats:
                            if c['name'].lower() == data['category_name'].lower() or \
                               data['category_name'].lower() in c['name'].lower():
                                ctx.user_data['category_id'] = str(c['id'])
                                ctx.user_data['_category_name'] = c['name']
                                break
                    except Exception as e:
                        log.error("Category lookup failed: %s", e)

                await update.message.reply_text("✅ Template parsed successfully!")
                return await self.confirm_prompt(update, ctx)

        # Fallback to normal name entry
        return await self.ask_product_code(update, ctx)

    async def ask_lengths(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        if update.message.text.strip() != "/skip":
            ctx.user_data["colors"] = self.split_csv(update.message.text)
        await update.message.reply_text("Step 11 — *Lengths*? (e.g. 10inch) — or /skip", parse_mode="Markdown")
        return ASK_LENGTHS

    async def ask_bundles(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        if update.message.text.strip() != "/skip":
            ctx.user_data["lengths"] = self.split_csv(update.message.text)
        await update.message.reply_text("Step 12 — *Bundles*? (e.g. 1 Bundle) — or /skip", parse_mode="Markdown")
        return ASK_BUNDLES

    async def ask_cap_sizes(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        if update.message.text.strip() != "/skip":
            ctx.user_data["bundles"] = self.split_csv(update.message.text)
        await update.message.reply_text("Step 13 — *Cap sizes*? (e.g. Small, Medium) — or /skip", parse_mode="Markdown")
        return ASK_CAP_SIZES

    async def ask_images(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        if update.message.text.strip() != "/skip":
            ctx.user_data["unavailable_lengths"] = self.split_csv(update.message.text)
        await update.message.reply_text(
            "📸 *Step 16 — Upload images*\n\nSend photos one by one (max 10).\nSend /done when finished.",
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
        optional_fields = (
            "product_name", "product_code", "original_price", "description", 
            "category_id", "badge", "colors", "lengths", "bundles", 
            "cap_sizes", "parting_options", "styling", "unavailable_lengths", "videos"
        )
        for key in optional_fields:
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
                text=f"🎉 *Product created!*\n\n• Name: {p.get('name')}\n• Slug: `{slug}`\n• Price: ${p.get('price'):,.0f}\n\n🔗 https://cmhairbyhills.org/product/{slug}",
                parse_mode="Markdown",
            )
        except Exception as exc:
            log.error("Product creation failed. Payload: %s, Error: %s", payload, exc)
            await ctx.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Failed: {exc}", parse_mode="Markdown")
        return ConversationHandler.END

    async def cancel(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("❌ Cancelled. Use /addproduct to start again.")
        return ConversationHandler.END

    def build(self) -> ConversationHandler:
        txt = filters.TEXT & ~filters.COMMAND
        return ConversationHandler(
            entry_points=[
                CommandHandler("addproduct", self.start),
                CommandHandler("template", self.show_template_example),
            ],
            states={
                ASK_NAME:           [
                    MessageHandler(filters.PHOTO | txt, self.handle_template_or_name),
                    CommandHandler("template", self.show_template_example)
                ],
                ASK_PRODUCT_CODE:   [MessageHandler(txt, self.ask_slug), CommandHandler("skip", self.ask_slug)],
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
                ASK_CAP_SIZES:      [MessageHandler(txt, self.ask_parting), CommandHandler("skip", self.ask_parting)],
                ASK_PARTING:        [MessageHandler(txt, self.ask_styling), CommandHandler("skip", self.ask_styling)],
                ASK_STYLING:        [MessageHandler(txt, self.ask_unavailable_lengths), CommandHandler("skip", self.ask_unavailable_lengths)],
                ASK_UNAVAILABLE_LENGTHS: [MessageHandler(txt, self.ask_images), CommandHandler("skip", self.ask_images)],
                ASK_IMAGES:         [MessageHandler(filters.PHOTO, self.receive_image), CommandHandler("done", self.confirm_prompt)],
                ASK_CONFIRM:        [CallbackQueryHandler(self.receive_confirm, pattern=r"^confirm:")],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
        )
