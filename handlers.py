from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationTypes
from database import Database
from study_modes import StudyModes
from spaced_repetition import SpacedRepetition
from gamification import Gamification
from datetime import datetime, timedelta
import random

db = Database()
user_states = {}

# Состояния для ConversationHandler
(
    MAIN_MENU, CREATE_DECK, ADD_CARD, STUDY_SELECT_MODE,
    STUDY_WRITE, STUDY_QUIZ, STUDY_FLASHCARD, DECK_MENU,
    EDIT_CARD, SETTINGS, IMPORT_CARDS, BROWSE_DICTIONARY
) = range(12)

# ==================== ГЛАВНОЕ МЕНЮ ====================

def get_main_menu_keyboard():
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("📚 Мои колоды", callback_data="my_decks")],
        [InlineKeyboardButton("➕ Создать колоду", callback_data="create_deck")],
        [InlineKeyboardButton("📖 Общий словарь", callback_data="browse_dict")],
        [InlineKeyboardButton("📊 Статистика", callback_data="my_stats")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    db.add_user(user_id, username)
    Gamification.init_user(user_id)
    
    welcome_text = """
🎓 *Добро пожаловать в QuizletBot!*

Я помогу вам эффективно учить слова с помощью:
• 🎴 Карточек с переворотом
• ✍️ Письменных упражнений  
• 🎯 Тестов с вариантами
• 🧠 Интервального повторения
• 🎮 Игровых механик

*Выберите действие ниже:*
    """
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    
    return MAIN_MENU

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка главного меню"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    if data == "my_decks":
        return await show_decks_menu(update, context)
    elif data == "create_deck":
        return await start_create_deck(update, context)
    elif data == "browse_dict":
        return await browse_dictionary(update, context)
    elif data == "my_stats":
        return await show_full_stats(update, context)
    elif data == "settings":
        return await show_settings(update, context)
    elif data == "help":
        return await show_help(update, context)
    elif data == "main_menu":
        return await start(update, context)
    
    return MAIN_MENU

# ==================== МОИ КОЛОДЫ ====================

async def show_decks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню колод"""
    user_id = update.effective_user.id
    decks = db.get_user_decks(user_id)
    
    if not decks:
        keyboard = [
            [InlineKeyboardButton("➕ Создать первую колоду", callback_data="create_deck")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ]
        await update.callback_query.edit_message_text(
            "📚 У вас пока нет колод.\n\nСоздайте первую колоду или выберите из общего словаря!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MAIN_MENU
    
    text = "📚 *Ваши колоды:*\n\n"
    keyboard = []
    
    for deck in decks:
        progress = SpacedRepetition.get_deck_progress(user_id, deck['deck_id'])
        text += f"📖 *{deck['name']}*\n"
        text += f"   📝 {deck['card_count']} карточек | 📊 {progress}% выучено\n\n"
        keyboard.append([InlineKeyboardButton(f"📖 {deck['name']}", callback_data=f"deck_menu_{deck['deck_id']}")])
    
    keyboard.append([InlineKeyboardButton("➕ Создать колоду", callback_data="create_deck")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])
    
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return MAIN_MENU

# ==================== МЕНЮ КОЛОДЫ ====================

async def deck_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню конкретной колоды"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    if data.startswith("deck_menu_"):
        deck_id = int(data.split("_")[2])
        context.user_data['current_deck_id'] = deck_id
        
        deck_info = db.get_deck_info(deck_id)
        cards = db.get_deck_cards(deck_id)
        
        # Статистика по колоде
        stats = SpacedRepetition.get_detailed_stats(user_id, deck_id)
        
        text = f"""
📖 *{deck_info['name']}*

📝 Всего карточек: {len(cards)}
✅ Выучено: {stats['mastered']}
🔄 На изучении: {stats['learning']}
⏰ На повторении: {stats['review']}
📊 Прогресс: {stats['progress']}%

*Выберите действие:*
        """
        
        keyboard = [
            [InlineKeyboardButton("🎓 Учиться", callback_data=f"study_select_{deck_id}")],
            [InlineKeyboardButton("🎴 Режим карточек", callback_data=f"study_flash_{deck_id}")],
            [InlineKeyboardButton("✍️ Письменный режим", callback_data=f"study_write_{deck_id}")],
            [InlineKeyboardButton("🎯 Тест", callback_data=f"study_quiz_{deck_id}")],
            [InlineKeyboardButton("🎮 Смешанный режим", callback_data=f"study_mixed_{deck_id}")],
            [InlineKeyboardButton("➕ Добавить карточки", callback_data=f"add_cards_{deck_id}")],
            [InlineKeyboardButton("📋 Список карточек", callback_data=f"list_cards_{deck_id}")],
            [InlineKeyboardButton("🗑 Удалить колоду", callback_data=f"delete_deck_{deck_id}")],
            [InlineKeyboardButton("⬅️ Назад к колодам", callback_data="my_decks")]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return DECK_MENU
    
    elif data.startswith("study_select_"):
        return await select_study_mode(update, context)
    elif data.startswith("study_flash_"):
        return await start_flashcard_mode(update, context)
    elif data.startswith("study_write_"):
        return await start_write_mode(update, context)
    elif data.startswith("study_quiz_"):
        return await start_quiz_mode(update, context)
    elif data.startswith("study_mixed_"):
        return await start_mixed_mode(update, context)
    elif data.startswith("add_cards_"):
        return await start_add_cards(update, context)
    elif data.startswith("list_cards_"):
        return await list_cards(update, context)
    elif data.startswith("delete_deck_"):
        return await confirm_delete_deck(update, context)

# ==================== РЕЖИМЫ ОБУЧЕНИЯ ====================

async def select_study_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор режима обучения"""
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    context.user_data['current_deck_id'] = deck_id
    
    text = """
🎓 *Выберите режим обучения:*

🎴 *Карточки* - переворачивайте и оценивайте
✍️ *Письменный* - вводите ответ с клавиатуры
🎯 *Тест* - выбирайте из 4 вариантов
🎮 *Смешанный* - случайный режим каждый раз
🧠 *Интервалы* - умное повторение по алгоритму
    """
    
    keyboard = [
        [InlineKeyboardButton("🎴 Карточки", callback_data=f"study_flash_{deck_id}")],
        [InlineKeyboardButton("✍️ Письменный", callback_data=f"study_write_{deck_id}")],
        [InlineKeyboardButton("🎯 Тест", callback_data=f"study_quiz_{deck_id}")],
        [InlineKeyboardButton("🎮 Смешанный", callback_data=f"study_mixed_{deck_id}")],
        [InlineKeyboardButton("🧠 Интервалы", callback_data=f"study_interval_{deck_id}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"deck_menu_{deck_id}")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return STUDY_SELECT_MODE

# Режим карточек (переворот)
async def start_flashcard_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    
    cards = StudyModes.prepare_cards(user_id, deck_id, mode='flashcard')
    
    if not cards:
        await query.edit_message_text("В колоде нет карточек! Добавьте их сначала.")
        return DECK_MENU
    
    context.user_data['study_session'] = {
        'mode': 'flashcard',
        'deck_id': deck_id,
        'cards': cards,
        'current': 0,
        'correct': 0,
        'wrong': 0,
        'flipped': False
    }
    
    await show_flashcard(query, user_id)
    return STUDY_FLASHCARD

async def show_flashcard(query, user_id):
    session = user_states[user_id]['study_session']
    card = session['cards'][session['current']]
    total = len(session['cards'])
    current = session['current'] + 1
    
    if session['flipped']:
        text = f"""
🎴 *Карточка {current}/{total}*

❓ {card['question']}

✅ *Ответ:* {card['answer']}

*Оцените, как хорошо вы знали:*
        """
        keyboard = [
            [
                InlineKeyboardButton("😞 Снова", callback_data="rate_again"),
                InlineKeyboardButton("😐 Трудно", callback_data="rate_hard"),
                InlineKeyboardButton("🙂 Хорошо", callback_data="rate_good"),
                InlineKeyboardButton("😄 Легко", callback_data="rate_easy")
            ]
        ]
    else:
        text = f"""
🎴 *Карточка {current}/{total}*

❓ *{card['question']}*

        """
        keyboard = [[InlineKeyboardButton("🔄 Показать ответ", callback_data="flip_card")]]
    
    keyboard.append([InlineKeyboardButton("⏹ Завершить", callback_data="stop_study")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Письменный режим
async def start_write_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    
    cards = StudyModes.prepare_cards(user_id, deck_id, mode='write')
    
    if not cards:
        await query.edit_message_text("В колоде нет карточек!")
        return DECK_MENU
    
    context.user_data['study_session'] = {
        'mode': 'write',
        'deck_id': deck_id,
        'cards': cards,
        'current': 0,
        'correct': 0,
        'wrong': 0
    }
    
    await ask_write_question(query, user_id)
    return STUDY_WRITE

async def ask_write_question(query, user_id):
    session = user_states[user_id]['study_session']
    card = session['cards'][session['current']]
    total = len(session['cards'])
    current = session['current'] + 1
    
    text = f"""
✍️ *Письменный режим {current}/{total}*

❓ *{card['question']}*

Напишите ответ сообщением:
    """
    
    keyboard = [[InlineKeyboardButton("⏹ Завершить", callback_data="stop_study")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def check_write_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка письменного ответа"""
    user_id = update.effective_user.id
    user_answer = update.message.text.strip().lower()
    session = context.user_data.get('study_session')
    
    if not session or session['mode'] != 'write':
        return MAIN_MENU
    
    card = session['cards'][session['current']]
    correct_answer = card['answer'].strip().lower()
    
    # Проверка с учетом опечаток (расстояние Левенштейна)
    similarity = StudyModes.calculate_similarity(user_answer, correct_answer)
    
    if similarity >= 0.8:  # 80% совпадение
        session['correct'] += 1
        SpacedRepetition.update_card_progress(user_id, card['card_id'], 'correct')
        
        # Очки и стрик
        points = Gamification.add_points(user_id, 'correct_write')
        streak = Gamification.update_streak(user_id)
        
        text = f"""
✅ *Правильно!* +{points} очков
        
Ваш ответ: {user_answer}
Правильный: {correct_answer}

🔥 Серия: {streak}
        """
        keyboard = [[InlineKeyboardButton("➡️ Далее", callback_data="next_card")]]
        
    elif similarity >= 0.5:
        session['correct'] += 0.5
        text = f"""
⚠️ *Почти правильно!*
        
Ваш ответ: {user_answer}
Правильный: {correct_answer}

Попробуйте еще раз или идите дальше?
        """
        keyboard = [
            [InlineKeyboardButton("🔄 Повторить", callback_data="retry_card")],
            [InlineKeyboardButton("➡️ Далее", callback_data="next_card")]
        ]
    else:
        session['wrong'] += 1
        SpacedRepetition.update_card_progress(user_id, card['card_id'], 'wrong')
        
        text = f"""
❌ *Неправильно*
        
Ваш ответ: {user_answer}
Правильный: *{correct_answer}*

Попробуйте еще раз?
        """
        keyboard = [
            [InlineKeyboardButton("🔄 Повторить", callback_data="retry_card")],
            [InlineKeyboardButton("💡 Показать подсказку", callback_data="show_hint")],
            [InlineKeyboardButton("➡️ Далее", callback_data="next_card")]
        ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return STUDY_WRITE

# Тестовый режим
async def start_quiz_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    
    cards = StudyModes.prepare_cards(user_id, deck_id, mode='quiz')
    
    if not cards:
        await query.edit_message_text("В колоде нет карточек!")
        return DECK_MENU
    
    context.user_data['study_session'] = {
        'mode': 'quiz',
        'deck_id': deck_id,
        'cards': cards,
        'current': 0,
        'correct': 0,
        'wrong': 0
    }
    
    await show_quiz_question(query, user_id)
    return STUDY_QUIZ

async def show_quiz_question(query, user_id):
    session = user_states[user_id]['study_session']
    card = session['cards'][session['current']]
    total = len(session['cards'])
    current = session['current'] + 1
    
    # Генерируем варианты ответа
    options = StudyModes.generate_quiz_options(card, session['cards'])
    
    text = f"""
🎯 *Тест {current}/{total}*

❓ *{card['question']}*

Выберите правильный ответ:
    """
    
    # Располагаем кнопки в 2 колонки
    keyboard = []
    row = []
    for i, option in enumerate(options):
        callback = "quiz_correct" if option == card['answer'] else f"quiz_wrong_{i}"
        row.append(InlineKeyboardButton(option, callback_data=callback))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("⏹ Завершить", callback_data="stop_study")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Смешанный режим
async def start_mixed_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    
    cards = StudyModes.prepare_cards(user_id, deck_id, mode='mixed')
    
    if not cards:
        await query.edit_message_text("В колоде нет карточек!")
        return DECK_MENU
    
    # Случайно выбираем режим для каждой карточки
    for card in cards:
        card['mode'] = random.choice(['flashcard', 'write', 'quiz'])
    
    context.user_data['study_session'] = {
        'mode': 'mixed',
        'deck_id': deck_id,
        'cards': cards,
        'current': 0,
        'correct': 0,
        'wrong': 0
    }
    
    await show_mixed_card(query, user_id)

async def show_mixed_card(query, user_id):
    session = user_states[user_id]['study_session']
    card = session['cards'][session['current']]
    
    if card['mode'] == 'flashcard':
        await show_flashcard(query, user_id)
    elif card['mode'] == 'write':
        await ask_write_question(query, user_id)
    else:
        await show_quiz_question(query, user_id)

# ==================== СОЗДАНИЕ КОЛОД ====================

async def start_create_deck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать создание колоды"""
    query = update.callback_query
    await query.answer()
    
    text = """
➕ *Создание новой колоды*

Введите название колоды:
(например: "Английские слова", "География", "Медицина")
    """
    
    await query.edit_message_text(text, parse_mode="Markdown")
    return CREATE_DECK

async def create_deck_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить название колоды"""
    user_id = update.effective_user.id
    deck_name = update.message.text.strip()
    
    if len(deck_name) < 2:
        await update.message.reply_text("❌ Название слишком короткое. Введите еще раз:")
        return CREATE_DECK
    
    deck_id = db.create_deck(user_id, deck_name)
    context.user_data['new_deck_id'] = deck_id
    context.user_data['new_deck_name'] = deck_name
    
    text = f"""
✅ *Колода "{deck_name}" создана!*

Теперь добавьте карточки.
Формат: *Вопрос | Ответ*

Примеры:
• Hello | Привет
• Столица Франции | Париж
• 2 + 2 | 4

Введите карточки по одной. Напишите "готово" когда закончите.
    """
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ADD_CARD

async def add_card_to_deck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить карточку в колоду"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if text.lower() == 'готово':
        return await finish_adding_cards(update, context)
    
    if '|' not in text:
        await update.message.reply_text("❌ Неправильный формат! Используйте: *Вопрос | Ответ*")
        return ADD_CARD
    
    parts = text.split('|', 1)
    question = parts[0].strip()
    answer = parts[1].strip()
    
    if not question or not answer:
        await update.message.reply_text("❌ Вопрос и ответ не могут быть пустыми!")
        return ADD_CARD
    
    deck_id = context.user_data.get('new_deck_id')
    card_id = db.add_card(deck_id, question, answer)
    
    # Инициализируем прогресс карточки
    SpacedRepetition.init_card(user_id, card_id)
    
    count = len(db.get_deck_cards(deck_id))
    
    text = f"""
✅ *Карточка добавлена!* ({count} всего)

❓ {question}
✏️ {answer}

Введите следующую или "готово"
    """
    
    keyboard = [[InlineKeyboardButton("✅ Завершить", callback_data="finish_adding")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ADD_CARD

async def finish_adding_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершить добавление карточек"""
    deck_id = context.user_data.get('new_deck_id')
    deck_name = context.user_data.get('new_deck_name')
    deck_info = db.get_deck_info(deck_id)
    
    text = f"""
🎉 *Колода "{deck_name}" готова!*

📊 Добавлено карточек: {deck_info['card_count']}

Что дальше?
    """
    
    keyboard = [
        [InlineKeyboardButton("🎓 Начать учить", callback_data=f"study_select_{deck_id}")],
        [InlineKeyboardButton("➕ Добавить еще", callback_data=f"add_cards_{deck_id}")],
        [InlineKeyboardButton("📚 Мои колоды", callback_data="my_decks")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return MAIN_MENU

# ==================== СТАТИСТИКА ====================

async def show_full_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Полная статистика"""
    query = update.callback_query
    user_id = query.from_user.id
    
    stats = Gamification.get_full_stats(user_id)
    study_stats = db.get_user_stats(user_id)
    
    text = f"""
📊 *Ваша статистика*

🎯 *Общий прогресс:*
• Колод создано: {study_stats['decks_count']}
• Карточек выучено: {stats['mastered_cards']}
• На изучении: {stats['learning_cards']}
• Точность: {study_stats['accuracy']}%

🎮 *Игровая статистика:*
• ⭐ Всего очков: {stats['total_points']}
• 🔥 Текущая серия: {stats['current_streak']}
• 🏆 Рекорд серии: {stats['max_streak']}
• 📅 Дней подряд: {stats['study_days_streak']}

📈 *Активность:*
• Всего сессий: {study_stats['total_studied']}
• Правильных ответов: {study_stats['total_correct']}
• Последнее обучение: {study_stats.get('last_studied', 'Никогда')[:10] if study_stats.get('last_studied') else 'Никогда'}
    """
    
    keyboard = [
        [InlineKeyboardButton("📊 Детальный прогресс", callback_data="detailed_progress")],
        [InlineKeyboardButton("🏆 Достижения", callback_data="achievements")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return MAIN_MENU

# ==================== ОБЩИЙ СЛОВАРЬ ====================

async def browse_dictionary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Общий словарь"""
    query = update.callback_query
    
    text = """
📖 *Общий словарь*

Выберите готовую коллекцию слов:
    """
    
    # Предустановленные коллекции
    collections = [
        ("🇬🇧 Английский - базовые", "english_basic"),
        ("🇬🇧 Английский - продвинутый", "english_advanced"),
        ("🇩🇪 Немецкий - базовый", "german_basic"),
        ("📊 Математика", "math_basic"),
        ("🌍 География", "geography"),
        ("🧬 Биология", "biology"),
        ("💼 Бизнес термины", "business"),
        ("💻 IT термины", "it_terms")
    ]
    
    keyboard = []
    for name, data in collections:
        keyboard.append([InlineKeyboardButton(name, callback_data=f"import_collection_{data}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return BROWSE_DICTIONARY

# ==================== НАСТРОЙКИ ====================

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройки"""
    query = update.callback_query
    user_id = query.from_user.id
    
    settings = db.get_user_settings(user_id)
    
    text = """
⚙️ *Настройки*

*Текущие параметры:*
• 🔔 Уведомления: {'Вкл' if settings.get('notifications') else 'Выкл'}
• 🎯 Сложность: {settings.get('difficulty', 'Средняя')}
• 🎴 Карточек в сессии: {settings.get('cards_per_session', 20)}
• ⏰ Время напоминания: {settings.get('reminder_time', '20:00')}
    """
    
    keyboard = [
        [InlineKeyboardButton("🔔 Уведомления", callback_data="toggle_notifications")],
        [InlineKeyboardButton("🎯 Сложность", callback_data="change_difficulty")],
        [InlineKeyboardButton("🎴 Карточек за раз", callback_data="change_session_size")],
        [InlineKeyboardButton("⏰ Напоминания", callback_data="change_reminder")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return SETTINGS

# ==================== ПОМОЩЬ ====================

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    query = update.callback_query
    
    text = """
❓ *Помощь по боту*

*Команды:*
/start - Главное меню
/decks - Мои колоды
/stats - Статистика
/help - Эта помощь

*Режимы обучения:*
🎴 *Карточки* - смотрите вопрос, переворачивайте, оценивайте знание
✍️ *Письменный* - вводите ответ, проверяется автоматически
🎯 *Тест* - выбирайте из 4 вариантов
🎮 *Смешанный* - разные режимы для разнообразия
🧠 *Интервалы* - умное повторение по алгоритму

*Советы:*
• Учите каждый день для поддержания серии 🔥
• Используйте разные режимы для лучшего запоминания
• Добавляйте свои карточки для персонализации
• Проверяйте статистику для отслеживания прогресса
    """
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return MAIN_MENU

# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена действия"""
    await update.message.reply_text("❌ Действие отменено", reply_markup=get_main_menu_keyboard())
    return MAIN_MENU

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений вне режимов"""
    # Проверяем, есть ли активная сессия обучения
    user_id = update.effective_user.id
    session = context.user_data.get('study_session')
    
    if session and session.get('mode') == 'write':
        return await check_write_answer(update, context)
    
    # Если нет активной сессии, показываем меню
    await update.message.reply_text(
        "Используйте меню для навигации:",
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU
