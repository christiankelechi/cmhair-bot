"""
cmhair-bot — Telegram admin bot for CMHair By Hills product management.
Entry point. Run with: python bot.py
"""

import logging
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes

import api
from config import TELEGRAM_BOT_TOKEN
from handlers import (
    build_add_product_handler,
    build_bulk_product_handler,
    build_add_category_handler,
    build_auth_handler,
    list_categories,
    logout_command,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


# ── Core commands ──────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    name = ctx.user_data.get("user_name")
    greeting = f"👋 Welcome back, *{name}*!" if name else "👋 Welcome to *CMHair Admin Bot*!"
    await update.message.reply_text(
        f"{greeting}\n\n"
        "🔐 *Auth*\n"
        "• /login — Log in with your admin account\n"
        "• /logout — Log out\n\n"
        "📦 *Products*\n"
        "• /addproduct — Add single product via template\n"
        "• /bulkproduct — Bulk upload via Excel\n\n"
        "📂 *Categories*\n"
        "• /categories — List categories\n"
        "• /addcategory — Create a category\n\n"
        "• /cancel — Cancel current operation",
        parse_mode="Markdown",
    )


async def cmd_whoami(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    name = ctx.user_data.get("user_name")
    roles = ctx.user_data.get("roles", [])
    if name:
        await update.message.reply_text(
            f"✅ Logged in as *{name}*\nRoles: {', '.join(roles)}",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("⛔ Not logged in. Use /login.")


# ── Bot setup ──────────────────────────────────────────────────────────────────

async def post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("start", "Help & welcome"),
        BotCommand("login", "Log in with your admin account"),
        BotCommand("logout", "Log out"),
        BotCommand("whoami", "Check who you're logged in as"),
        BotCommand("addproduct", "Add single product via template"),
        BotCommand("bulkproduct", "Bulk upload via Excel"),
        BotCommand("template", "Show product entry template"),
        BotCommand("categories", "List categories"),
        BotCommand("addcategory", "Create a category"),
        BotCommand("cancel", "Cancel current operation"),
    ])
    log.info("🤖 CMHair bot started. Users must /login to use admin features.")


def main() -> None:
    # Build with a longer request timeout (20s) for Telegram API calls
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).read_timeout(20).write_timeout(20).connect_timeout(20).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("whoami", cmd_whoami))
    app.add_handler(CommandHandler("logout", logout_command))
    app.add_handler(CommandHandler("categories", list_categories))

    app.add_handler(build_auth_handler())
    app.add_handler(build_add_product_handler())
    app.add_handler(build_bulk_product_handler())
    app.add_handler(build_add_category_handler())

    log.info("Polling for updates…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
