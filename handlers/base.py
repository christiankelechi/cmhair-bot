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
    def slugify(text: str, max_len: int = 80) -> str:
        s = re.sub(r"[^a-z0-9\s-]", "", text.lower().strip())
        return re.sub(r"\s+", "-", s)[:max_len]

    @staticmethod
    def split_csv(text: str) -> list[str]:
        return [x.strip() for x in text.split(",") if x.strip()]

    @staticmethod
    def summary(d: dict) -> str:
        lines = [
            "📦 *Product Summary*",
            f"• *Name:* {d.get('name')}",
            f"• *Slug:* `{d.get('slug')}`",
            f"• *Price:* ₦{d.get('price'):,.0f}",
        ]
        if d.get("original_price"):
            lines.append(f"• *Original Price:* ₦{d['original_price']:,.0f}")
        lines.append(f"• *Stock:* {d.get('stock', 0)}")
        if d.get("description"):
            lines.append(f"• *Description:* {d['description'][:120]}")
        if d.get("_category_name"):
            lines.append(f"• *Category:* {d['_category_name']}")
        if d.get("badge"):
            lines.append(f"• *Badge:* {d['badge']}")
        for field in ("colors", "lengths", "bundles", "cap_sizes"):
            if d.get(field):
                lines.append(f"• *{field.replace('_', ' ').title()}:* {', '.join(d[field])}")
        lines.append(f"• *Images:* {len(d.get('images', []))} uploaded")
        return "\n".join(lines)
