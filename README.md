# cmhair-bot 🤖

A Telegram admin bot for **CMHair By Hills** — lets you add products with photos directly from Telegram, just like the web admin panel.

---

## Prerequisites

- Python **3.11+**
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- Your cmhair admin account credentials

---

## Setup

### 1. Install dependencies

```bash
cd cmhair-bot
pip install -r requirements.txt
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Open `.env` and fill in:

| Key | Value |
|-----|-------|
| `TELEGRAM_BOT_TOKEN` | From @BotFather → `/newbot` |
| `TELEGRAM_ADMIN_CHAT_IDS` | Your numeric Telegram ID (from @userinfobot), comma-separated |
| `API_BASE_URL` | `https://cyberswitchapp-services.duckdns.org` |
| `ADMIN_EMAIL` | Your admin account email |
| `ADMIN_PASSWORD` | Your admin account password |

### 3. Run the bot

```bash
python bot.py
```

---

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message & help |
| `/addproduct` | Start the multi-step add-product wizard |
| `/categories` | List all product categories |
| `/addcategory` | Create a new category |
| `/status` | Check API connection |
| `/cancel` | Cancel the current operation |
| `/skip` | Skip optional fields during product creation |
| `/done` | Finish uploading images and move to confirmation |

---

## Add-Product Flow

```
/addproduct
  → Product name
  → Slug (auto-suggested, you can override)
  → Price ($)
  → Original price (optional)
  → Stock quantity
  → Description (optional)
  → Category (inline keyboard)
  → Badge — new / sale / bestseller / limited / none (inline keyboard)
  → Colors (comma-separated, optional)
  → Lengths (comma-separated, optional)
  → Bundle sizes (comma-separated, optional)
  → Cap sizes (comma-separated, optional)
  → Photos → send one by one, /done when finished
  → Confirmation card → ✅ Confirm / ❌ Cancel
  → Product created 🎉
```

Images are uploaded directly to **Cloudinary** via the `/upload/image` endpoint and the secure URLs are stored on the product.

---

## Security

Set `TELEGRAM_ADMIN_CHAT_IDS` to your numeric Telegram user ID(s) to restrict bot access. Leave blank only for private/test bots.

---

## Running on a Server (optional)

To keep the bot running, use a simple systemd service or run with `screen` / `tmux`:

```bash
screen -S cmhair-bot
python bot.py
# Detach: Ctrl+A, D
```
