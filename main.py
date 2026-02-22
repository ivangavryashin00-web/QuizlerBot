import logging
import os
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Импорты
from database import Database
from handlers import (
    start, main_menu_callback, deck_menu_callback, message_handler,
    select_study_mode, start_flashcard_mode, start_write_mode, 
    start_quiz_mode, start_mixed_mode, start_create_deck, create_deck_name,
    add_card_to_deck, finish_adding_cards, show_full_stats, browse_dictionary,
    show_settings, show_help, cancel,
    MAIN_MENU, CREATE_DECK, ADD_CARD, STUDY_SELECT_MODE, STUDY_WRITE,
    STUDY_QUIZ, STUDY_FLASHCARD, DECK_MENU, SETTINGS, BROWSE_DICTIONARY
)

def main():
    """Запуск бота"""
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    # Инициализация БД
    db = Database()
    db.init_db()
    
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("decks", lambda u, c: start(u, c) if u.message else main_menu_callback(u, c)),
        ],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(main_menu_callback, pattern="^(my_decks|create_deck|browse_dict|my_stats|settings|help|main_menu)$")
            ],
            DECK_MENU: [
                CallbackQueryHandler(deck_menu_callback, pattern="^deck_menu_"),
                CallbackQueryHandler(deck_menu_callback, pattern="^study_"),
                CallbackQueryHandler(deck_menu_callback, pattern="^add_cards_"),
                CallbackQueryHandler(deck_menu_callback, pattern="^list_cards_"),
                CallbackQueryHandler(deck_menu_callback, pattern="^delete_deck_"),
            ],
            STUDY_SELECT_MODE: [
                CallbackQueryHandler(select_study_mode, pattern="^study_select_"),
                CallbackQueryHandler(start_flashcard_mode, pattern="^study_flash_"),
                CallbackQueryHandler(start_write_mode, pattern="^study_write_"),
                CallbackQueryHandler(start_quiz_mode, pattern="^study_quiz_"),
                CallbackQueryHandler(start_mixed_mode, pattern="^study_mixed_"),
            ],
            STUDY_FLASHCARD: [
                CallbackQueryHandler(deck_menu_callback, pattern="^(flip_card|rate_|stop_study|next_card)"),
            ],
            STUDY_WRITE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
                CallbackQueryHandler(deck_menu_callback, pattern="^(stop_study|next_card|retry_card|show_hint)"),
            ],
            STUDY_QUIZ: [
                CallbackQueryHandler(deck_menu_callback, pattern="^(quiz_|stop_study)"),
            ],
            CREATE_DECK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, create_deck_name),
                CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"),
            ],
            ADD_CARD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_card_to_deck),
                CallbackQueryHandler(finish_adding_cards, pattern="^finish_adding$"),
            ],
            SETTINGS: [
                CallbackQueryHandler(show_settings, pattern="^toggle_|change_"),
                CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"),
            ],
            BROWSE_DICTIONARY: [
                CallbackQueryHandler(browse_dictionary, pattern="^import_collection_"),
                CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
        ],
    )
    
    application.add_handler(conv_handler)
    
    # Отдельные команды
    application.add_handler(CommandHandler("help", show_help))
    application.add_handler(CommandHandler("stats", show_full_stats))
    
    logger.info("🚀 Бот запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()
