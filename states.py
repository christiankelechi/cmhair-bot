"""
Conversation states for all handlers.
"""

# ── Add Product States ─────────────────────────────────────────────────────────
(
    ASK_NAME,
    ASK_SLUG,
    ASK_PRICE,
    ASK_ORIGINAL_PRICE,
    ASK_STOCK,
    ASK_DESCRIPTION,
    ASK_CATEGORY,
    ASK_BADGE,
    ASK_COLORS,
    ASK_LENGTHS,
    ASK_BUNDLES,
    ASK_CAP_SIZES,
    ASK_IMAGES,
    ASK_CONFIRM,
) = range(14)

# ── Add Category States ────────────────────────────────────────────────────────
(
    CAT_NAME,
    CAT_SLUG,
    CAT_DESCRIPTION,
    CAT_CONFIRM,
) = range(100, 104)

# ── Auth States ────────────────────────────────────────────────────────────────
(
    AUTH_EMAIL,
    AUTH_PASSWORD,
) = range(200, 202)
