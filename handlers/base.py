"""Shared base class for all bot handlers."""
import re
from telegram import Update
from telegram.ext import ContextTypes


class BaseHandler:

    @staticmethod
    def token(ctx: ContextTypes.DEFAULT_TYPE) -> str | None:
        return ctx.user_data.get("token")

    @staticmethod
    async def require_auth(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
        """Returns True if logged in, otherwise sends an error and returns False."""
        if ctx.user_data.get("token"):
            return True
        await update.message.reply_text(
            "⛔ *Not logged in.*\n\nUse /login to authenticate with your admin account.",
            parse_mode="Markdown",
        )
        return False

    @staticmethod
    def slugify(name: str, product_code: str = None, max_len: int = 80) -> str:
        import time
        import random
        import string
        
        # Base name slug
        s = re.sub(r"[^a-z0-9\s-]", "", name.lower().strip())
        slug = re.sub(r"\s+", "-", s)
        
        # Add product code if available to make it more intuitive
        if product_code:
            code_s = re.sub(r"[^a-z0-9]", "", product_code.lower().strip())
            if code_s:
                slug = f"{slug}-{code_s}"
        
        # Append timestamp + random suffix (8 chars total)
        suffix = f"{int(time.time() % 1000):03d}" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        
        full_slug = f"{slug}-{suffix}"
        return full_slug[:max_len]

    @staticmethod
    def split_csv(text: str) -> list[str]:
        return [x.strip() for x in text.split(",") if x.strip()]

    @staticmethod
    def summary(d: dict) -> str:
        lines = [
            "📦 *Product Summary*",
            f"• *Name:* {d.get('name')}",
            f"• *Product Code:* {d.get('product_code', 'N/A')}",
            f"• *Slug:* `{d.get('slug')}`",
            f"• *Price:* ${d.get('price', 0):,.0f}",
        ]
        if d.get("original_price"):
            lines.append(f"• *Original Price:* ${d['original_price']:,.0f}")
        lines.append(f"• *Stock:* {d.get('stock', 0)}")
        if d.get("description"):
            lines.append(f"• *Description:* {d['description'][:120]}")
        if d.get("_category_name"):
            lines.append(f"• *Category:* {d['_category_name']}")
        if d.get("badge"):
            lines.append(f"• *Badge:* {d['badge']}")
        
        for field in ("colors", "lengths", "bundles", "cap_sizes", "parting_options", "styling", "unavailable_lengths"):
            if d.get(field):
                label = field.replace('_', ' ').replace('options', '').strip().title()
                lines.append(f"• *{label}:* {', '.join(d[field])}")
                
        lines.append(f"• *Images:* {len(d.get('images', []))} uploaded")
        return "\n".join(lines)
