from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import Database
from study_modes import StudyModes
from spaced_repetition import SpacedRepetition
from gamification import Gamification
from datetime import datetime
import random

db = Database()

# Состояния для ConversationHandler
(
    MAIN_MENU, CREATE_DECK, ADD_CARD, STUDY_SELECT_MODE,
    STUDY_WRITE, STUDY_QUIZ, STUDY_FLASHCARD, DECK_MENU,
    EDIT_CARD, SETTINGS, IMPORT_CARDS, BROWSE_DICTIONARY
) = range(12)

# ==================== ГЛАВНОЕ МЕНЮ ====================

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📚 Мои колоды", callback_data="my_decks"),
         InlineKeyboardButton("➕ Создать колоду", callback_data="create_deck")],
        [InlineKeyboardButton("📖 Общий словарь", callback_data="browse_dict"),
         InlineKeyboardButton("📊 Статистика", callback_data="my_stats")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
         InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    db.add_user(user_id, username)
    Gamification.init_user(user_id)

    welcome_text = (
        "🎓 *Добро пожаловать в QuizletBot!*\n\n"
        "Я помогу вам эффективно учить материал:\n"
        "• 🎴 Карточки с переворотом\n"
        "• ✍️ Письменные упражнения\n"
        "• 🎯 Тесты с вариантами\n"
        "• 🧠 Интервальное повторение\n"
        "• 🎮 Игровые механики и достижения\n\n"
        "*Выберите действие:*"
    )

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    return MAIN_MENU

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

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
    user_id = update.effective_user.id
    decks = db.get_user_decks(user_id)

    if not decks:
        keyboard = [
            [InlineKeyboardButton("➕ Создать первую колоду", callback_data="create_deck")],
            [InlineKeyboardButton("📖 Общий словарь", callback_data="browse_dict")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ]
        await update.callback_query.edit_message_text(
            "📚 У вас пока нет колод.\n\nСоздайте первую колоду или выберите готовую из словаря!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MAIN_MENU

    text = "📚 *Ваши колоды:*\n\n"
    keyboard = []

    for deck in decks:
        progress = SpacedRepetition.get_deck_progress(user_id, deck['deck_id'])
        bar = _progress_bar(progress)
        text += f"📖 *{deck['name']}* — {deck['card_count']} карт. {bar} {progress}%\n"
        keyboard.append([InlineKeyboardButton(f"📖 {deck['name']} ({deck['card_count']} карт.)", callback_data=f"deck_menu_{deck['deck_id']}")])

    keyboard.append([InlineKeyboardButton("➕ Создать колоду", callback_data="create_deck"),
                     InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])

    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return MAIN_MENU

def _progress_bar(percent, length=5):
    filled = round(percent / 100 * length)
    return "█" * filled + "░" * (length - filled)

# ==================== МЕНЮ КОЛОДЫ ====================

async def deck_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data.startswith("deck_menu_"):
        deck_id = int(data.split("_")[2])
        context.user_data['current_deck_id'] = deck_id
        return await show_deck_menu(update, context, deck_id)

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
    elif data.startswith("confirm_delete_"):
        return await do_delete_deck(update, context)

    # Обработка действий в сессии обучения
    elif data == "flip_card":
        return await handle_flip_card(update, context)
    elif data.startswith("rate_"):
        return await handle_rate_card(update, context)
    elif data == "next_card":
        return await handle_next_card(update, context)
    elif data == "retry_card":
        return await handle_retry_card(update, context)
    elif data == "show_hint":
        return await handle_show_hint(update, context)
    elif data == "stop_study":
        return await stop_study_session(update, context)
    elif data.startswith("quiz_"):
        return await handle_quiz_answer(update, context)

    return DECK_MENU

async def show_deck_menu(update, context, deck_id):
    user_id = update.effective_user.id
    deck_info = db.get_deck_info(deck_id)
    if not deck_info:
        await update.callback_query.edit_message_text("❌ Колода не найдена.")
        return MAIN_MENU

    stats = SpacedRepetition.get_detailed_stats(user_id, deck_id)
    bar = _progress_bar(stats['progress'])

    text = (
        f"📖 *{deck_info['name']}*\n\n"
        f"📝 Всего карточек: *{stats['total']}*\n"
        f"✅ Выучено: {stats['mastered']} | 🔄 Изучается: {stats['learning']} | ⏰ Повторить: {stats['review']}\n"
        f"📊 Прогресс: {bar} {stats['progress']}%\n\n"
        f"*Выберите действие:*"
    )

    keyboard = [
        [InlineKeyboardButton("🎓 Выбрать режим", callback_data=f"study_select_{deck_id}")],
        [InlineKeyboardButton("🎴 Карточки", callback_data=f"study_flash_{deck_id}"),
         InlineKeyboardButton("✍️ Письменный", callback_data=f"study_write_{deck_id}")],
        [InlineKeyboardButton("🎯 Тест", callback_data=f"study_quiz_{deck_id}"),
         InlineKeyboardButton("🎮 Смешанный", callback_data=f"study_mixed_{deck_id}")],
        [InlineKeyboardButton("➕ Добавить карточки", callback_data=f"add_cards_{deck_id}")],
        [InlineKeyboardButton("📋 Список карточек", callback_data=f"list_cards_{deck_id}"),
         InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_deck_{deck_id}")],
        [InlineKeyboardButton("⬅️ К колодам", callback_data="my_decks")]
    ]

    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return DECK_MENU

# ==================== РЕЖИМЫ ОБУЧЕНИЯ ====================

async def select_study_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    context.user_data['current_deck_id'] = deck_id

    text = (
        "🎓 *Выберите режим обучения:*\n\n"
        "🎴 *Карточки* — переворот и оценка\n"
        "✍️ *Письменный* — вводите ответ\n"
        "🎯 *Тест* — 4 варианта ответа\n"
        "🎮 *Смешанный* — разные режимы\n"
        "🧠 *Интервалы* — умный алгоритм"
    )

    keyboard = [
        [InlineKeyboardButton("🎴 Карточки", callback_data=f"study_flash_{deck_id}"),
         InlineKeyboardButton("✍️ Письменный", callback_data=f"study_write_{deck_id}")],
        [InlineKeyboardButton("🎯 Тест", callback_data=f"study_quiz_{deck_id}"),
         InlineKeyboardButton("🎮 Смешанный", callback_data=f"study_mixed_{deck_id}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"deck_menu_{deck_id}")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return STUDY_SELECT_MODE

# ---- Flashcard ----

async def start_flashcard_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_cards(user_id, deck_id, mode='flashcard')

    if not cards:
        await query.edit_message_text("❌ В колоде нет карточек!")
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

    await _show_flashcard(query, context)
    return STUDY_FLASHCARD

async def _show_flashcard(query, context):
    session = context.user_data['study_session']
    card = session['cards'][session['current']]
    total = len(session['cards'])
    current = session['current'] + 1

    if session.get('flipped'):
        text = (
            f"🎴 *Карточка {current}/{total}*\n\n"
            f"❓ {card['question']}\n\n"
            f"✅ *Ответ:* {card['answer']}\n\n"
            f"*Оцените, как вы знали:*"
        )
        keyboard = [
            [
                InlineKeyboardButton("😞 Снова", callback_data="rate_again"),
                InlineKeyboardButton("😐 Трудно", callback_data="rate_hard"),
                InlineKeyboardButton("🙂 Хорошо", callback_data="rate_good"),
                InlineKeyboardButton("😄 Легко", callback_data="rate_easy")
            ],
            [InlineKeyboardButton("⏹ Завершить", callback_data="stop_study")]
        ]
    else:
        text = (
            f"🎴 *Карточка {current}/{total}*\n\n"
            f"❓ *{card['question']}*\n\n"
            f"Подумайте и переверните карточку"
        )
        keyboard = [
            [InlineKeyboardButton("🔄 Показать ответ", callback_data="flip_card")],
            [InlineKeyboardButton("⏹ Завершить", callback_data="stop_study")]
        ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_flip_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = context.user_data.get('study_session')
    if not session:
        return MAIN_MENU
    session['flipped'] = True
    await _show_flashcard(update.callback_query, context)
    return STUDY_FLASHCARD

async def handle_rate_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    session = context.user_data.get('study_session')
    if not session:
        return MAIN_MENU

    rating = query.data.split("_")[1]  # again, hard, good, easy
    card = session['cards'][session['current']]

    result_map = {'again': 'again', 'hard': 'wrong', 'good': 'correct', 'easy': 'correct'}
    SpacedRepetition.update_card_progress(user_id, card['card_id'], result_map[rating])

    if rating in ['good', 'easy']:
        session['correct'] += 1
        Gamification.add_points(user_id, 'correct_flashcard')
        Gamification.update_streak(user_id)
    else:
        session['wrong'] += 1

    session['current'] += 1
    session['flipped'] = False

    if session['current'] >= len(session['cards']):
        return await _finish_session(query, context, user_id)

    await _show_flashcard(query, context)
    return STUDY_FLASHCARD

# ---- Write ----

async def start_write_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_cards(user_id, deck_id, mode='write')

    if not cards:
        await query.edit_message_text("❌ В колоде нет карточек!")
        return DECK_MENU

    context.user_data['study_session'] = {
        'mode': 'write',
        'deck_id': deck_id,
        'cards': cards,
        'current': 0,
        'correct': 0,
        'wrong': 0
    }

    await _ask_write_question(query, context)
    return STUDY_WRITE

async def _ask_write_question(query, context):
    session = context.user_data['study_session']
    card = session['cards'][session['current']]
    total = len(session['cards'])
    current = session['current'] + 1

    text = (
        f"✍️ *Письменный режим {current}/{total}*\n\n"
        f"❓ *{card['question']}*\n\n"
        f"Напишите ответ:"
    )
    keyboard = [[InlineKeyboardButton("⏹ Завершить", callback_data="stop_study")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def check_write_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_answer = update.message.text.strip()
    session = context.user_data.get('study_session')

    if not session or session.get('mode') != 'write':
        await update.message.reply_text("Используйте меню:", reply_markup=get_main_menu_keyboard())
        return MAIN_MENU

    card = session['cards'][session['current']]
    correct_answer = card['answer'].strip()
    similarity = StudyModes.calculate_similarity(user_answer, correct_answer)

    if similarity >= 0.85:
        session['correct'] += 1
        SpacedRepetition.update_card_progress(user_id, card['card_id'], 'correct')
        points = Gamification.add_points(user_id, 'correct_write')
        streak = Gamification.update_streak(user_id)
        text = (
            f"✅ *Правильно!* +{points} очков 🔥 Серия: {streak}\n\n"
            f"Ваш: _{user_answer}_\nПравильный: *{correct_answer}*"
        )
        keyboard = [[InlineKeyboardButton("➡️ Далее", callback_data="next_card")]]
    elif similarity >= 0.5:
        text = (
            f"⚠️ *Почти!*\n\n"
            f"Ваш: _{user_answer}_\nПравильный: *{correct_answer}*"
        )
        keyboard = [
            [InlineKeyboardButton("🔄 Повторить", callback_data="retry_card"),
             InlineKeyboardButton("➡️ Далее", callback_data="next_card")]
        ]
    else:
        session['wrong'] += 1
        SpacedRepetition.update_card_progress(user_id, card['card_id'], 'wrong')
        hint = StudyModes.get_hint(correct_answer)
        text = (
            f"❌ *Неправильно*\n\n"
            f"Ваш: _{user_answer}_\nПравильный: *{correct_answer}*\n\nПодсказка: {hint}"
        )
        keyboard = [
            [InlineKeyboardButton("🔄 Повторить", callback_data="retry_card"),
             InlineKeyboardButton("➡️ Далее", callback_data="next_card")]
        ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return STUDY_WRITE

async def handle_next_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    session = context.user_data.get('study_session')
    if not session:
        return MAIN_MENU

    session['current'] += 1
    if session['current'] >= len(session['cards']):
        return await _finish_session(query, context, user_id)

    mode = session['mode']
    if mode == 'write':
        await _ask_write_question(query, context)
        return STUDY_WRITE
    elif mode == 'quiz':
        await _show_quiz_question(query, context)
        return STUDY_QUIZ
    elif mode == 'mixed':
        return await _show_mixed_card(query, context)
    else:
        session['flipped'] = False
        await _show_flashcard(query, context)
        return STUDY_FLASHCARD

async def handle_retry_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    session = context.user_data.get('study_session')
    if not session:
        return MAIN_MENU
    mode = session.get('mode', 'write')
    if mode == 'write':
        await _ask_write_question(query, context)
        return STUDY_WRITE
    return STUDY_FLASHCARD

async def handle_show_hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    session = context.user_data.get('study_session')
    if not session:
        return MAIN_MENU
    card = session['cards'][session['current']]
    hint = StudyModes.get_hint(card['answer'], 0.4)
    await query.answer(f"💡 Подсказка: {hint}", show_alert=True)
    return STUDY_WRITE

# ---- Quiz ----

async def start_quiz_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_cards(user_id, deck_id, mode='quiz')

    if not cards:
        await query.edit_message_text("❌ В колоде нет карточек!")
        return DECK_MENU

    if len(cards) < 2:
        await query.edit_message_text("❌ Для теста нужно минимум 2 карточки!")
        return DECK_MENU

    context.user_data['study_session'] = {
        'mode': 'quiz',
        'deck_id': deck_id,
        'cards': cards,
        'current': 0,
        'correct': 0,
        'wrong': 0
    }

    await _show_quiz_question(query, context)
    return STUDY_QUIZ

async def _show_quiz_question(query, context):
    session = context.user_data['study_session']
    card = session['cards'][session['current']]
    total = len(session['cards'])
    current = session['current'] + 1

    options = StudyModes.generate_quiz_options(card, session['cards'])

    text = (
        f"🎯 *Тест {current}/{total}*\n\n"
        f"❓ *{card['question']}*\n\n"
        f"Выберите правильный ответ:"
    )

    keyboard = []
    row = []
    for i, option in enumerate(options):
        callback = "quiz_correct" if option == card['answer'] else f"quiz_wrong_{i}"
        # Truncate long options for button text
        btn_text = option[:30] + "…" if len(option) > 30 else option
        row.append(InlineKeyboardButton(btn_text, callback_data=callback))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⏹ Завершить", callback_data="stop_study")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    session = context.user_data.get('study_session')
    if not session:
        return MAIN_MENU

    data = query.data
    card = session['cards'][session['current']]

    if data == "quiz_correct":
        session['correct'] += 1
        SpacedRepetition.update_card_progress(user_id, card['card_id'], 'correct')
        points = Gamification.add_points(user_id, 'correct_quiz')
        await query.answer(f"✅ Правильно! +{points} очков", show_alert=False)
    else:
        session['wrong'] += 1
        SpacedRepetition.update_card_progress(user_id, card['card_id'], 'wrong')
        await query.answer(f"❌ Неверно! Правильный: {card['answer']}", show_alert=True)

    session['current'] += 1
    if session['current'] >= len(session['cards']):
        return await _finish_session(query, context, user_id)

    await _show_quiz_question(query, context)
    return STUDY_QUIZ

# ---- Mixed ----

async def start_mixed_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_cards(user_id, deck_id, mode='mixed')

    if not cards:
        await query.edit_message_text("❌ В колоде нет карточек!")
        return DECK_MENU

    modes = ['flashcard', 'quiz'] if len(cards) < 2 else ['flashcard', 'write', 'quiz']
    for card in cards:
        card['sub_mode'] = random.choice(modes)

    context.user_data['study_session'] = {
        'mode': 'mixed',
        'deck_id': deck_id,
        'cards': cards,
        'current': 0,
        'correct': 0,
        'wrong': 0,
        'flipped': False
    }

    return await _show_mixed_card(query, context)

async def _show_mixed_card(query, context):
    session = context.user_data['study_session']
    card = session['cards'][session['current']]
    sub_mode = card.get('sub_mode', 'flashcard')

    if sub_mode == 'write':
        await _ask_write_question(query, context)
        return STUDY_WRITE
    elif sub_mode == 'quiz':
        await _show_quiz_question(query, context)
        return STUDY_QUIZ
    else:
        session['flipped'] = False
        await _show_flashcard(query, context)
        return STUDY_FLASHCARD

# ---- Session finish ----

async def _finish_session(query, context, user_id):
    session = context.user_data.get('study_session', {})
    deck_id = session.get('deck_id')
    correct = session.get('correct', 0)
    wrong = session.get('wrong', 0)
    total = correct + wrong

    accuracy = round(correct / total * 100) if total > 0 else 0

    db.record_study_session(user_id, deck_id, int(correct), total)

    if accuracy == 100 and total >= 3:
        Gamification.add_points(user_id, 'perfect_session')
        bonus = "\n🏆 *Идеальная сессия!* +50 бонусных очков!"
    else:
        bonus = ""

    text = (
        f"🎉 *Сессия завершена!*\n\n"
        f"✅ Правильно: {int(correct)}/{total}\n"
        f"📊 Точность: {accuracy}%\n"
        f"{'🔥 Отличный результат!' if accuracy >= 80 else '💪 Продолжайте практиковаться!'}"
        f"{bonus}"
    )

    keyboard = [
        [InlineKeyboardButton("🔄 Ещё раз", callback_data=f"study_select_{deck_id}")],
        [InlineKeyboardButton("📚 Мои колоды", callback_data="my_decks"),
         InlineKeyboardButton("🏠 Главная", callback_data="main_menu")]
    ]

    context.user_data.pop('study_session', None)
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return MAIN_MENU

async def stop_study_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    return await _finish_session(query, context, user_id)

# ==================== УПРАВЛЕНИЕ КАРТОЧКАМИ ====================

async def start_add_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    context.user_data['new_deck_id'] = deck_id
    deck_info = db.get_deck_info(deck_id)
    context.user_data['new_deck_name'] = deck_info['name'] if deck_info else 'Колода'

    text = (
        f"➕ *Добавление карточек в «{deck_info['name']}»*\n\n"
        f"Формат: *Вопрос | Ответ*\n\n"
        f"Примеры:\n"
        f"• Hello | Привет\n"
        f"• Столица Франции | Париж\n"
        f"• 2 + 2 | 4\n\n"
        f"Напишите «готово» или нажмите кнопку для завершения."
    )

    keyboard = [[InlineKeyboardButton("✅ Завершить", callback_data="finish_adding")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ADD_CARD

async def list_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    cards = db.get_deck_cards(deck_id)
    deck_info = db.get_deck_info(deck_id)

    if not cards:
        await query.answer("В колоде нет карточек", show_alert=True)
        return DECK_MENU

    text = f"📋 *Карточки в «{deck_info['name']}»:*\n\n"
    for i, card in enumerate(cards[:30], 1):
        q = card['question'][:40] + "…" if len(card['question']) > 40 else card['question']
        a = card['answer'][:40] + "…" if len(card['answer']) > 40 else card['answer']
        text += f"{i}. ❓ {q}\n   ✅ {a}\n"

    if len(cards) > 30:
        text += f"\n_...и ещё {len(cards)-30} карточек_"

    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=f"deck_menu_{deck_id}")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return DECK_MENU

async def confirm_delete_deck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    deck_info = db.get_deck_info(deck_id)

    text = (
        f"⚠️ *Удалить колоду «{deck_info['name']}»?*\n\n"
        f"Это удалит все {deck_info['card_count']} карточек и прогресс.\n"
        f"*Действие необратимо!*"
    )
    keyboard = [
        [InlineKeyboardButton("🗑 Да, удалить", callback_data=f"confirm_delete_{deck_id}"),
         InlineKeyboardButton("❌ Отмена", callback_data=f"deck_menu_{deck_id}")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return DECK_MENU

async def do_delete_deck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    deck_id = int(query.data.split("_")[2])
    db.delete_deck(deck_id, user_id)
    await query.answer("✅ Колода удалена", show_alert=False)
    return await show_decks_menu(update, context)

# ==================== СОЗДАНИЕ КОЛОД ====================

async def start_create_deck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "➕ *Создание новой колоды*\n\n"
        "Введите название колоды:\n"
        "_Например: «Английские слова», «История», «Химия»_"
    )
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return CREATE_DECK

async def create_deck_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    deck_name = update.message.text.strip()

    if len(deck_name) < 2:
        await update.message.reply_text("❌ Название слишком короткое. Введите ещё раз:")
        return CREATE_DECK

    if len(deck_name) > 50:
        await update.message.reply_text("❌ Название слишком длинное (макс. 50 символов):")
        return CREATE_DECK

    deck_id = db.create_deck(user_id, deck_name)
    context.user_data['new_deck_id'] = deck_id
    context.user_data['new_deck_name'] = deck_name

    text = (
        f"✅ *Колода «{deck_name}» создана!*\n\n"
        f"Теперь добавьте карточки.\n"
        f"Формат: *Вопрос | Ответ*\n\n"
        f"Примеры:\n"
        f"• Hello | Привет\n"
        f"• Столица Франции | Париж\n\n"
        f"Напишите «готово» или нажмите кнопку для завершения."
    )
    keyboard = [[InlineKeyboardButton("✅ Завершить", callback_data="finish_adding")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ADD_CARD

async def add_card_to_deck(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text.lower() in ('готово', 'done', '/done'):
        return await finish_adding_cards(update, context)

    if '|' not in text:
        await update.message.reply_text(
            "❌ Используйте формат: *Вопрос | Ответ*\nНапример: Hello | Привет",
            parse_mode="Markdown"
        )
        return ADD_CARD

    parts = text.split('|', 1)
    question = parts[0].strip()
    answer = parts[1].strip()

    if not question or not answer:
        await update.message.reply_text("❌ Вопрос и ответ не могут быть пустыми!")
        return ADD_CARD

    deck_id = context.user_data.get('new_deck_id')
    if not deck_id:
        await update.message.reply_text("❌ Ошибка: колода не найдена. Начните заново.")
        return MAIN_MENU

    card_id = db.add_card(deck_id, question, answer)
    SpacedRepetition.init_card(user_id, card_id)
    count = len(db.get_deck_cards(deck_id))

    reply = (
        f"✅ *Карточка добавлена!* ({count} всего)\n\n"
        f"❓ {question}\n"
        f"✅ {answer}\n\n"
        f"Введите следующую или «готово»"
    )
    keyboard = [[InlineKeyboardButton("✅ Завершить", callback_data="finish_adding")]]
    await update.message.reply_text(reply, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ADD_CARD

async def finish_adding_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deck_id = context.user_data.get('new_deck_id')
    deck_name = context.user_data.get('new_deck_name', 'Колода')

    if deck_id:
        deck_info = db.get_deck_info(deck_id)
        count = deck_info['card_count'] if deck_info else 0
    else:
        count = 0

    text = (
        f"🎉 *Колода «{deck_name}» готова!*\n\n"
        f"📊 Добавлено карточек: {count}\n\n"
        f"Что дальше?"
    )

    keyboard = [
        [InlineKeyboardButton("🎓 Начать учить", callback_data=f"study_select_{deck_id}")],
        [InlineKeyboardButton("➕ Добавить ещё", callback_data=f"add_cards_{deck_id}"),
         InlineKeyboardButton("📚 Мои колоды", callback_data="my_decks")]
    ]

    # Can come from message or callback
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return MAIN_MENU

# ==================== СТАТИСТИКА ====================

async def show_full_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        user_id = query.from_user.id
    else:
        user_id = update.effective_user.id

    stats = Gamification.get_full_stats(user_id)
    study_stats = db.get_user_stats(user_id)

    last_studied = study_stats.get('last_studied')
    last_str = last_studied[:10] if last_studied else 'Никогда'

    text = (
        f"📊 *Ваша статистика*\n\n"
        f"📚 *Прогресс:*\n"
        f"• Колод создано: {study_stats['decks_count']}\n"
        f"• Карточек выучено: {stats['mastered_cards']}\n"
        f"• На изучении: {stats['learning_cards']}\n"
        f"• Точность: {study_stats['accuracy']}%\n\n"
        f"🎮 *Игровая статистика:*\n"
        f"• ⭐ Очков: {stats['total_points']}\n"
        f"• 🔥 Текущая серия: {stats['current_streak']} дней\n"
        f"• 🏆 Рекорд серии: {stats['max_streak']} дней\n"
        f"• 📅 Всего дней обучения: {stats['study_days_streak']}\n\n"
        f"📈 *Активность:*\n"
        f"• Всего попыток: {study_stats['total_attempts']}\n"
        f"• Правильных: {study_stats['total_correct']}\n"
        f"• Последнее занятие: {last_str}"
    )

    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return MAIN_MENU

# ==================== СЛОВАРЬ ====================

COLLECTIONS = {
    "english_basic": {
        "name": "🇬🇧 Английский (базовый)",
        "cards": [
            ("Hello", "Привет"), ("Goodbye", "Пока"), ("Thank you", "Спасибо"),
            ("Please", "Пожалуйста"), ("Yes", "Да"), ("No", "Нет"),
            ("Water", "Вода"), ("Food", "Еда"), ("House", "Дом"),
            ("Car", "Машина"), ("Book", "Книга"), ("Time", "Время"),
            ("Day", "День"), ("Night", "Ночь"), ("Friend", "Друг"),
            ("Family", "Семья"), ("Work", "Работа"), ("School", "Школа"),
            ("Good", "Хороший"), ("Bad", "Плохой")
        ]
    },
    "english_advanced": {
        "name": "🇬🇧 Английский (продвинутый)",
        "cards": [
            ("Ambiguous", "Неоднозначный"), ("Ephemeral", "Мимолётный"),
            ("Eloquent", "Красноречивый"), ("Pragmatic", "Прагматичный"),
            ("Resilient", "Устойчивый"), ("Nuanced", "Нюансированный"),
            ("Obsolete", "Устаревший"), ("Profound", "Глубокий"),
            ("Scrutiny", "Тщательная проверка"), ("Tenacious", "Настойчивый"),
            ("Ubiquitous", "Повсеместный"), ("Verbose", "Многословный"),
            ("Whimsical", "Причудливый"), ("Zealous", "Рьяный"),
            ("Alacrity", "Живость"), ("Benevolent", "Доброжелательный")
        ]
    },
    "math_basic": {
        "name": "📊 Математика",
        "cards": [
            ("Что такое периметр?", "Сумма всех сторон фигуры"),
            ("Формула площади прямоугольника", "S = a × b"),
            ("Теорема Пифагора", "a² + b² = c²"),
            ("Формула дискриминанта", "D = b² - 4ac"),
            ("π (пи) ≈", "3.14159"),
            ("Формула длины окружности", "L = 2πr"),
            ("Формула площади круга", "S = πr²"),
            ("Сумма углов треугольника", "180°"),
            ("Производная x²", "2x"),
            ("Интеграл от x", "x²/2 + C")
        ]
    },
    "it_terms": {
        "name": "💻 IT термины",
        "cards": [
            ("Algorithm", "Алгоритм — набор инструкций для решения задачи"),
            ("API", "Application Programming Interface — интерфейс программирования"),
            ("Backend", "Серверная часть приложения"),
            ("Frontend", "Клиентская часть (интерфейс)"),
            ("Database", "База данных"),
            ("Git", "Система контроля версий"),
            ("HTTP", "Протокол передачи гипертекста"),
            ("JSON", "JavaScript Object Notation — формат данных"),
            ("SDK", "Software Development Kit — набор инструментов разработчика"),
            ("UI/UX", "User Interface / User Experience")
        ]
    },
    "geography": {
        "name": "🌍 География",
        "cards": [
            ("Столица России", "Москва"), ("Столица Франции", "Париж"),
            ("Столица Германии", "Берлин"), ("Столица Японии", "Токио"),
            ("Самая длинная река", "Нил (или Амазонка)"),
            ("Самая высокая гора", "Эверест (8849 м)"),
            ("Самый большой океан", "Тихий океан"),
            ("Самый большой материк", "Евразия"),
            ("Столица Австралии", "Канберра"),
            ("Столица Бразилии", "Бразилиа")
        ]
    },
    "biology": {
        "name": "🧬 Биология",
        "cards": [
            ("Что такое ДНК?", "Дезоксирибонуклеиновая кислота — носитель генетической информации"),
            ("Функция митохондрий", "Выработка энергии (АТФ) — «электростанция» клетки"),
            ("Что такое фотосинтез?", "Процесс преобразования света в химическую энергию растениями"),
            ("Из чего состоит клетка?", "Ядро, цитоплазма, мембрана, органеллы"),
            ("Что такое ген?", "Участок ДНК, кодирующий признак"),
            ("Функция гемоглобина", "Перенос кислорода в крови"),
            ("Что такое экосистема?", "Совокупность организмов и среды их обитания"),
            ("Типы размножения", "Половое и бесполое")
        ]
    },
    "business": {
        "name": "💼 Бизнес термины",
        "cards": [
            ("ROI", "Return on Investment — возврат на инвестиции"),
            ("KPI", "Key Performance Indicator — ключевой показатель эффективности"),
            ("B2B", "Business to Business — бизнес для бизнеса"),
            ("B2C", "Business to Consumer — бизнес для потребителя"),
            ("CRM", "Customer Relationship Management — управление отношениями с клиентами"),
            ("MVP", "Minimum Viable Product — минимально жизнеспособный продукт"),
            ("SWOT", "Strengths, Weaknesses, Opportunities, Threats — анализ"),
            ("Маржа", "Разница между ценой продажи и себестоимостью"),
            ("Ликвидность", "Способность быстро продать актив по рыночной цене"),
            ("Диверсификация", "Распределение рисков по разным активам/направлениям")
        ]
    },
    "german_basic": {
        "name": "🇩🇪 Немецкий (базовый)",
        "cards": [
            ("Hallo", "Привет"), ("Danke", "Спасибо"), ("Bitte", "Пожалуйста"),
            ("Ja", "Да"), ("Nein", "Нет"), ("Wasser", "Вода"),
            ("Haus", "Дом"), ("Auto", "Машина"), ("Buch", "Книга"),
            ("Arbeit", "Работа"), ("Schule", "Школа"), ("Freund", "Друг"),
            ("Tag", "День"), ("Nacht", "Ночь"), ("Gut", "Хорошо"),
            ("Schlecht", "Плохо"), ("Danke schön", "Большое спасибо")
        ]
    }
}

async def browse_dictionary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.data.startswith("import_collection_"):
        return await import_collection(update, context)

    text = (
        "📖 *Общий словарь*\n\n"
        "Выберите готовую коллекцию:"
    )

    keyboard = []
    for key, col in COLLECTIONS.items():
        count = len(col['cards'])
        keyboard.append([InlineKeyboardButton(f"{col['name']} ({count} карт.)", callback_data=f"import_collection_{key}")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return BROWSE_DICTIONARY

async def import_collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    col_key = query.data.replace("import_collection_", "")

    collection = COLLECTIONS.get(col_key)
    if not collection:
        await query.answer("❌ Коллекция не найдена", show_alert=True)
        return BROWSE_DICTIONARY

    deck_id = db.create_deck(user_id, collection['name'])
    for question, answer in collection['cards']:
        card_id = db.add_card(deck_id, question, answer)
        SpacedRepetition.init_card(user_id, card_id)

    text = (
        f"✅ *Коллекция импортирована!*\n\n"
        f"📖 {collection['name']}\n"
        f"📝 Добавлено карточек: {len(collection['cards'])}\n\n"
        f"Хотите начать учить?"
    )
    keyboard = [
        [InlineKeyboardButton("🎓 Учить сейчас", callback_data=f"study_select_{deck_id}")],
        [InlineKeyboardButton("📖 Общий словарь", callback_data="browse_dict"),
         InlineKeyboardButton("📚 Мои колоды", callback_data="my_decks")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return MAIN_MENU

# ==================== НАСТРОЙКИ ====================

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    settings = db.get_user_settings(user_id)

    notif = "✅ Вкл" if settings.get('notifications', 1) else "❌ Выкл"
    diff = settings.get('difficulty', 'medium')
    diff_map = {'easy': '🟢 Лёгкая', 'medium': '🟡 Средняя', 'hard': '🔴 Сложная'}
    diff_str = diff_map.get(diff, '🟡 Средняя')
    per_session = settings.get('cards_per_session', 20)
    reminder = settings.get('reminder_time', '20:00')

    text = (
        f"⚙️ *Настройки*\n\n"
        f"• 🔔 Уведомления: {notif}\n"
        f"• 🎯 Сложность: {diff_str}\n"
        f"• 🎴 Карточек за сессию: {per_session}\n"
        f"• ⏰ Напоминание: {reminder}"
    )

    keyboard = [
        [InlineKeyboardButton(f"🔔 Уведомления: {notif}", callback_data="toggle_notifications")],
        [InlineKeyboardButton("🎯 Сложность", callback_data="change_difficulty")],
        [InlineKeyboardButton("➖ Меньше карточек", callback_data="cards_less"),
         InlineKeyboardButton("➕ Больше карточек", callback_data="cards_more")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return SETTINGS

async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "toggle_notifications":
        settings = db.get_user_settings(user_id)
        new_val = 0 if settings.get('notifications', 1) else 1
        db.update_user_setting(user_id, 'notifications', new_val)
        await query.answer("✅ Уведомления обновлены")
    elif data == "change_difficulty":
        settings = db.get_user_settings(user_id)
        diff_cycle = {'easy': 'medium', 'medium': 'hard', 'hard': 'easy'}
        new_diff = diff_cycle.get(settings.get('difficulty', 'medium'), 'medium')
        db.update_user_setting(user_id, 'difficulty', new_diff)
        await query.answer(f"Сложность изменена")
    elif data == "cards_less":
        settings = db.get_user_settings(user_id)
        new_val = max(5, settings.get('cards_per_session', 20) - 5)
        db.update_user_setting(user_id, 'cards_per_session', new_val)
        await query.answer(f"Карточек за сессию: {new_val}")
    elif data == "cards_more":
        settings = db.get_user_settings(user_id)
        new_val = min(50, settings.get('cards_per_session', 20) + 5)
        db.update_user_setting(user_id, 'cards_per_session', new_val)
        await query.answer(f"Карточек за сессию: {new_val}")

    return await show_settings(update, context)

# ==================== ПОМОЩЬ ====================

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        send = update.callback_query.edit_message_text
    else:
        send = update.message.reply_text

    text = (
        "❓ *Помощь по QuizletBot*\n\n"
        "*Команды:*\n"
        "/start — Главное меню\n"
        "/stats — Статистика\n"
        "/help — Эта помощь\n"
        "/cancel — Отмена действия\n\n"
        "*Режимы обучения:*\n"
        "🎴 *Карточки* — смотрите вопрос, переворачивайте, оценивайте\n"
        "✍️ *Письменный* — вводите ответ, проверяется автоматически\n"
        "🎯 *Тест* — выбирайте из 4 вариантов\n"
        "🎮 *Смешанный* — разные режимы для разнообразия\n\n"
        "*Создание карточек:*\n"
        "Формат: `Вопрос | Ответ`\n"
        "Пример: `Hello | Привет`\n\n"
        "*Советы:*\n"
        "• Учитесь каждый день для серии 🔥\n"
        "• Используйте разные режимы\n"
        "• Добавляйте карточки из словаря\n"
        "• Алгоритм автоматически подбирает сложность"
    )

    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]]
    await send(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return MAIN_MENU

# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Действие отменено", reply_markup=get_main_menu_keyboard())
    return MAIN_MENU

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = context.user_data.get('study_session')
    if session and session.get('mode') == 'write':
        return await check_write_answer(update, context)

    await update.message.reply_text(
        "Используйте меню для навигации:",
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU
