"""Auth handler — /login and /logout commands."""
import logging
import api
from telegram import Update
from telegram.ext import (
    CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters,
)
import httpx
from states import AUTH_EMAIL, AUTH_PASSWORD

log = logging.getLogger(__name__)
ADMIN_ROLES = {"engineer_admin"}


class AuthHandler:

    async def start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        ctx.user_data.pop("token", None)
        await update.message.reply_text(
            "🔐 *Login to CMHair Admin*\n\nEnter your *email address*:",
            parse_mode="Markdown",
        )
        return AUTH_EMAIL

    async def receive_email(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        ctx.user_data["_login_email"] = update.message.text.strip()
        await update.message.reply_text("🔑 Enter your *password*:", parse_mode="Markdown")
        return AUTH_PASSWORD

    async def receive_password(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        email = ctx.user_data.pop("_login_email", "")
        password = update.message.text.strip()

        # Delete password message immediately for security
        try:
            await update.message.delete()
        except Exception:
            pass

        msg = await ctx.bot.send_message(update.effective_chat.id, "⏳ Logging in…")
        try:
            result = await api.login_user(email, password)
            roles = set(result["roles"])

            if not roles & ADMIN_ROLES:
                await msg.edit_text(
                    "⛔ *Access Denied*\n\nYour account does not have **Engineer Admin** privileges.\n"
                    "Normal admins are not allowed to use this bot.\n"
                    "Contact the system administrator if you believe this is an error.",
                    parse_mode="Markdown",
                )
                return ConversationHandler.END

            ctx.user_data["token"] = result["token"]
            ctx.user_data["user_name"] = result["name"]
            ctx.user_data["roles"] = list(roles)

            role_label = "Engineer Admin" if "engineer_admin" in roles else "Admin"
            await msg.edit_text(
                f"✅ *Welcome, {result['name']}!*\n\n"
                f"Role: *{role_label}*\n\n"
                f"Use /addproduct to add a product or /start for all commands.",
                parse_mode="Markdown",
            )
        except httpx.ConnectTimeout:
            await msg.edit_text("⏳ *Connection Timeout*\n\nThe bot couldn't reach the server. Please check your internet or wait a moment and try again.", parse_mode="Markdown")
        except httpx.HTTPStatusError as e:
            await msg.edit_text(f"❌ *Server Error:* `{e.response.status_code}`\n\nTry again later.", parse_mode="Markdown")
        except Exception as exc:
            await msg.edit_text(f"❌ *Login failed:* `{exc}`\n\nTry /login again.", parse_mode="Markdown")

        return ConversationHandler.END

    async def cancel(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("❌ Login cancelled.")
        return ConversationHandler.END

    async def logout(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        ctx.user_data.pop("token", None)
        ctx.user_data.pop("user_name", None)
        ctx.user_data.pop("roles", None)
        await update.message.reply_text("👋 Logged out. Use /login to log back in.")

    def build(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("login", self.start)],
            states={
                AUTH_EMAIL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_email)],
                AUTH_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_password)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True,
        )


_h = AuthHandler()
build_auth_handler = _h.build
logout_command = _h.logout
