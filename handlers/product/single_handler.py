import logging
import uuid
from typing import Any
from telegram import Update
from telegram.ext import (
    CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
)
from handlers.base import BaseHandler
import api
from utils.parser import parse_template, get_template_example

log = logging.getLogger(__name__)

WAIT_INPUT = 1

class SingleProductHandler(BaseHandler):
    
    async def start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        if not await self.require_auth(update, ctx):
            return ConversationHandler.END
            
        ctx.user_data['pending_images'] = []
            
        template_text = get_template_example()
        msg = (
            "🛍️ *Add Single Product*\n\n"
            "Please send the product details formatted precisely like the template below.\n"
            "You can send it as a **text message**, OR upload an image and paste the template in its **caption**!\n\n"
            f"```text\n{template_text}\n```\n\n"
            "*(Send /cancel to abort)*"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return WAIT_INPUT

    async def process_template(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE, text: str) -> int:
        msg = await update.message.reply_text("⏳ Processing product template...")
        try:
            data = parse_template(text)
            
            name = data.get('name') or data.get('product_name')
            if not name:
                await msg.edit_text("❌ Could not find product name in the template. Please check the format.")
                return WAIT_INPUT
                
            slug = data.get('slug')
            if not slug:
                slug = self.slugify(name)
                
            uploaded_image_urls = []
            
            if update.message.photo:
                await msg.edit_text("⏳ Uploading attached image...")
                photo_file = await update.message.photo[-1].get_file()
                img_bytes = await photo_file.download_as_bytearray()
                filename = f"image_{uuid.uuid4().hex[:8]}.jpg"
                url = await api.upload_image(img_bytes, self.token(ctx), filename)
                uploaded_image_urls.append(url)
                
            pending_images = ctx.user_data.get('pending_images', [])
            if pending_images:
                await msg.edit_text(f"⏳ Uploading {len(pending_images)} previously sent image(s)...")
                for img_bytes in pending_images:
                    filename = f"image_{uuid.uuid4().hex[:8]}.jpg"
                    url = await api.upload_image(img_bytes, self.token(ctx), filename)
                    uploaded_image_urls.append(url)
                ctx.user_data['pending_images'] = []
                
            price = data.get('price', 0)
            orig_price = data.get('original_price', 0)
            if price == 0 and orig_price > 0:
                price = orig_price
                
            # Resolve category name → UUID
            category_name = data.get('category_name') or data.get('category')
            category_id = None
            if category_name:
                category_id = await api.resolve_category_id(category_name, self.token(ctx))
                
            payload = {
                "name": name,
                "product_name": name,
                "slug": slug,
                "product_code": data.get('product_code', ''),
                "price": price,
                "original_price": orig_price if orig_price > price else None,
                "stock": data.get('stock', 0),
                "is_preorder": data.get('is_preorder', False),
                "cap_sizes": data.get('cap_sizes', None),
                "lengths": data.get('lengths', None),
                "length_prices": data.get('length_prices', None),
                "bundles": data.get('bundles', None),
                "colors": data.get('colors', None),
                "images": uploaded_image_urls,
                "parting_options": data.get('parting_options', None),
                "description": data.get('description', ''),
                "category_id": category_id,
                "is_active": True,
            }
            
            await api.create_product(payload, self.token(ctx))
            await msg.edit_text(f"✅ *Product Created successfully!*\n\n• Name: {name}\n• Slug: `{slug}`\n• Price: ${price:,.0f}", parse_mode="Markdown")
            
        except Exception as e:
            log.error("Template processing failed: %s", e)
            await msg.edit_text(f"❌ Failed to process template: {str(e)}")
            
        return ConversationHandler.END

    async def handle_text(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text
        if text and text.count(':') >= 3:
            return await self.process_template(update, ctx, text)
        else:
            await update.message.reply_text("❌ Please send a valid template format (with at least 3 colons), or a Photo to queue images. Send /cancel to abort.")
            return WAIT_INPUT

    async def handle_photo(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        caption = update.message.caption
        if caption and caption.count(':') >= 3:
            return await self.process_template(update, ctx, caption)
            
        try:
            if 'pending_images' not in ctx.user_data:
                ctx.user_data['pending_images'] = []
                
            photo_file = await update.message.photo[-1].get_file()
            file_content = await photo_file.download_as_bytearray()
            ctx.user_data['pending_images'].append(file_content)
            
            count = len(ctx.user_data['pending_images'])
            await update.message.reply_text(f"✅ Queued Image #{count}. (Send more, or send the text template!)")
        except Exception as e:
            log.error("Failed to receive image bytes: %s", e)
            
        return WAIT_INPUT

    async def cancel(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        ctx.user_data['pending_images'] = []
        await update.message.reply_text("❌ Cancelled. Use /addproduct to start again.")
        return ConversationHandler.END

    def build(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("addproduct", self.start)],
            states={
                WAIT_INPUT: [
                    MessageHandler(filters.PHOTO, self.handle_photo),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
        )
