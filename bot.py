import asyncio
import logging
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)
from database.db import init_db
from handlers.main_handlers import (
    cmd_start, cmd_profile, cmd_inventory, cmd_archive, cmd_map, cmd_save, cmd_achievements,
    callback_language, callback_menu, callback_background, callback_psych,
    callback_starter_item, callback_char, callback_permadeath,
    callback_choice, callback_combat, callback_death, callback_stat, callback_settings,
    handle_text_input
)
from config import BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application: Application):
    await init_db()
    logger.info("✅ Database initialized")
    await application.bot.set_my_commands([
        ("start",   "🛸 Main Menu"),
        ("profilo", "👤 Character Profile"),
        ("inventario", "🎒 Inventory"),
        ("archivio", "📂 Lore Archive"),
        ("mappa",   "🗺️ Station Map"),
        ("obiettivi", "🏆 Achievements"),
        ("salva",   "💾 Save game"),
    ])


def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Set BOT_TOKEN in your .env file before running!")
        return

    app = (Application.builder()
           .token(BOT_TOKEN)
           .post_init(post_init)
           .build())

    # Commands
    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("profilo",     cmd_profile))
    app.add_handler(CommandHandler("profile",     cmd_profile))
    app.add_handler(CommandHandler("inventario",  cmd_inventory))
    app.add_handler(CommandHandler("inventory",   cmd_inventory))
    app.add_handler(CommandHandler("archivio",    cmd_archive))
    app.add_handler(CommandHandler("archive",     cmd_archive))
    app.add_handler(CommandHandler("mappa",       cmd_map))
    app.add_handler(CommandHandler("map",         cmd_map))
    app.add_handler(CommandHandler("salva",       cmd_save))
    app.add_handler(CommandHandler("save",        cmd_save))
    app.add_handler(CommandHandler("obiettivi",   cmd_achievements))
    app.add_handler(CommandHandler("achievements",cmd_achievements))

    # Callbacks — grouped by prefix
    app.add_handler(CallbackQueryHandler(callback_language,     pattern=r"^lang:"))
    app.add_handler(CallbackQueryHandler(callback_menu,         pattern=r"^menu:"))
    app.add_handler(CallbackQueryHandler(callback_background,   pattern=r"^bg:"))
    app.add_handler(CallbackQueryHandler(callback_psych,        pattern=r"^psych:"))
    app.add_handler(CallbackQueryHandler(callback_starter_item, pattern=r"^item:"))
    app.add_handler(CallbackQueryHandler(callback_char,         pattern=r"^char:"))
    app.add_handler(CallbackQueryHandler(callback_permadeath,   pattern=r"^permadeath:"))
    app.add_handler(CallbackQueryHandler(callback_choice,       pattern=r"^choice:"))
    app.add_handler(CallbackQueryHandler(callback_choice,       pattern=r"^locked$"))
    app.add_handler(CallbackQueryHandler(callback_combat,       pattern=r"^combat:"))
    app.add_handler(CallbackQueryHandler(callback_death,        pattern=r"^death:"))
    app.add_handler(CallbackQueryHandler(callback_stat,         pattern=r"^stat:"))
    app.add_handler(CallbackQueryHandler(callback_settings,     pattern=r"^settings:"))

    # Text input
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    logger.info("🛸 ALIEN: DARK SIGNAL — Bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
