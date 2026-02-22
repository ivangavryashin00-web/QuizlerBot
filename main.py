import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Импортируем обработчики
from handlers import (
    start, help_command, view_decks, view_stats,
    button_callback, message_handler
)

def main():
    """Запуск бота"""
    # Получаем токен из переменной окружения
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not TOKEN or TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    # Инициализация базы данных
    from database import Database
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
    
    logger.info("🚀 Бот запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()
