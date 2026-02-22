import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
from database import Database
from handlers import (
    start, help_command, view_decks, view_stats,
    button_callback, message_handler
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
CREATING_DECK = 1
ADDING_CARD = 2
STUDYING = 3
EDITING_CARD = 4

def main():
    """Запуск бота"""
    # Замени на свой токен от @BotFather
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    
    # Инициализация базы данных
    db = Database()
    db.init_db()
    
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("decks", view_decks))
    application.add_handler(CommandHandler("stats", view_stats))
    
    # Обработчик для кнопок
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Обработчик сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    logger.info("Бот запущен!")
    application.run_polling()

def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f"Update {update} caused error {context.error}")

if __name__ == '__main__':
    main()
