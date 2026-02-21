# Конфигурация для QuizletBot

# Telegram API
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Получите от @BotFather

# База данных
DATABASE_NAME = "quizlet_bot.db"
DATABASE_PATH = "./"

# Настройки обучения
MAX_CARDS_PER_SESSION = 50  # Максимум карточек в одной сессии
SHUFFLE_CARDS = True  # Перемешивать карточки при обучении
AUTO_SAVE = True  # Автосохранение прогресса

# UI Настройки
USE_EMOJIS = True  # Использовать эмодзи в сообщениях
DEFAULT_LANGUAGE = "ru"  # Язык по умолчанию (ru/en)

# Лимиты
MAX_DECKS_PER_USER = 100  # Максимум колод на пользователя
MAX_CARDS_PER_DECK = 500  # Максимум карточек в колоде
MAX_QUESTION_LENGTH = 1000  # Максимальная длина вопроса
MAX_ANSWER_LENGTH = 1000  # Максимальная длина ответа

# Логирование
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "bot.log"
