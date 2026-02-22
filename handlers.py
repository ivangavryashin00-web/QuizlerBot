from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from datetime import datetime
import random

db = Database()

# Сохраняем текущее состояние пользователя
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start - начало работы"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    db.add_user(user_id, username)
    user_states[user_id] = {'mode': 'main'}
    
    welcome_text = """
🎓 *Добро пожаловать в QuizletBot!*

Это бот для создания и изучения карточек со словами, определениями и вопросами.

*Основные команды:*
/help - Справка по командам
/decks - Мои колоды
/stats - Статистика обучения

Начни с команды /decks или создай новую колоду прямо сейчас! 📚
    """
    
    keyboard = [
        [InlineKeyboardButton("📚 Мои колоды", callback_data="view_decks")],
        [InlineKeyboardButton("➕ Создать колоду", callback_data="create_deck")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help - справка"""
    help_text = """
*📖 СПРАВКА ПО КОМАНДАМ*

*/start* - Начало работы
*/help* - Эта справка
*/decks* - Список ваших колод
*/stats* - Статистика обучения

*ОСНОВНЫЕ ВОЗМОЖНОСТИ:*

1️⃣ *Создание колоды*
   - Выберите "Создать колоду"
   - Введите название
   - Добавляйте карточки (вопрос + ответ)

2️⃣ *Обучение*
   - Выберите колоду
   - Переворачивайте карточки
   - Отмечайте "знаю" или "не знаю"

Начните обучение прямо сейчас! 🚀
    """
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def view_decks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /decks - просмотр колод"""
    user_id = update.effective_user.id
    decks = db.get_user_decks(user_id)
    
    if not decks:
        keyboard = [[InlineKeyboardButton("➕ Создать колоду", callback_data="create_deck")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "У вас нет колод. Создайте первую! 📚",
            reply_markup=reply_markup
        )
        return
    
    text = "📚 *Ваши колоды:*\n\n"
    keyboard = []
    
    for deck in decks:
        text += f"• *{deck['name']}* ({deck['card_count']} карточек)\n"
        keyboard.append([
            InlineKeyboardButton(f"📖 {deck['name']}", callback_data=f"deck_{deck['deck_id']}")
        ])
    
    keyboard.append([InlineKeyboardButton("➕ Создать колоду", callback_data="create_deck")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def view_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /stats - статистика"""
    user_id = update.effective_user.id
    stats = db.get_user_stats(user_id)
    
    last_studied = stats.get('last_studied', 'Никогда')
    if last_studied and last_studied != 'Никогда':
        last_studied = datetime.fromisoformat(last_studied).strftime('%d.%m.%Y %H:%M')
    
    text = f"""
📊 *Ваша статистика обучения:*

🎯 Колод создано: {stats['decks_count']}
📝 Карточек изучено: {stats['total_studied']}
✅ Правильных ответов: {stats['total_correct']}
📈 Всего попыток: {stats['total_attempts']}
🎓 Точность: {stats['accuracy']}%
🕐 Последнее обучение: {last_studied}
    """
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "create_deck":
        user_states[user_id] = {'mode': 'creating_deck'}
        await query.edit_message_text(text="📝 Введите название для новой колоды:")
    
    elif data == "view_decks":
        await view_decks_callback(query, user_id)
    
    elif data.startswith("deck_"):
        deck_id = int(data.split("_")[1])
        await view_deck_detail(query, user_id, deck_id)
    
    elif data.startswith("study_"):
        deck_id = int(data.split("_")[1])
        await start_study_mode(query, user_id, deck_id)
    
    elif data == "flip_card":
        await flip_card(query, user_id)
    
    elif data == "answer_correct":
        await answer_correct(query, user_id)
    
    elif data == "answer_wrong":
        await answer_wrong(query, user_id)
    
    elif data == "stop_study":
        await stop_study(query, user_id)
    
    elif data.startswith("add_card_"):
        deck_id = int(data.split("_")[2])
        user_states[user_id] = {'mode': 'adding_cards', 'deck_id': deck_id}
        await query.edit_message_text(
            "📝 Добавляйте карточки\nФормат: *Вопрос | Ответ*\n\nВведите 'готово' когда закончите."
        )
    
    elif data.startswith("list_cards_"):
        deck_id = int(data.split("_")[2])
        await list_cards_callback(query, deck_id)
    
    elif data.startswith("delete_card_"):
        parts = data.split("_")
        card_id = int(parts[2])
        deck_id = int(parts[3]) if len(parts) > 3 else None
        await delete_card_callback(query, user_id, card_id, deck_id)
    
    elif data.startswith("delete_deck_"):
        deck_id = int(data.split("_")[2])
        await delete_deck_callback(query, user_id, deck_id)
    
    elif data.startswith("confirm_delete_deck_"):
        deck_id = int(data.split("_")[3])
        db.delete_deck(deck_id, user_id)
        await query.edit_message_text("✅ Колода удалена! 🗑")
        await view_decks_callback(query, user_id)
    
    elif data == "stats":
        stats = db.get_user_stats(user_id)
        text = f"""
📊 *Ваша статистика:*

🎯 Колод: {stats['decks_count']}
📝 Изучено карточек: {stats['total_studied']}
✅ Правильных ответов: {stats['total_correct']}
📈 Всего попыток: {stats['total_attempts']}
🎓 Точность: {stats['accuracy']}%
        """
        keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="view_decks")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def view_decks_callback(query, user_id):
    """Просмотр колод в callback"""
    decks = db.get_user_decks(user_id)
    
    if not decks:
        keyboard = [[InlineKeyboardButton("➕ Создать", callback_data="create_deck")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="У вас нет колод. Создайте первую! 📚", reply_markup=reply_markup)
        return
    
    text = "📚 *Ваши колоды:*\n\n"
    keyboard = []
    
    for deck in decks:
        text += f"📖 *{deck['name']}* - {deck['card_count']} карточек\n"
        keyboard.append([InlineKeyboardButton(f"👉 {deck['name']}", callback_data=f"deck_{deck['deck_id']}")])
    
    keyboard.append([InlineKeyboardButton("➕ Создать колоду", callback_data="create_deck")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def view_deck_detail(query, user_id, deck_id):
    """Просмотр деталей колоды"""
    deck_info = db.get_deck_info(deck_id)
    
    if not deck_info:
        await query.edit_message_text("Колода не найдена 😕")
        return
    
    text = f"""
📖 *{deck_info['name']}*

Карточек: {deck_info['card_count']}
Создана: {datetime.fromisoformat(deck_info['created_at']).strftime('%d.%m.%Y')}
    """
    
    keyboard = [
        [InlineKeyboardButton("🎓 Учиться", callback_data=f"study_{deck_id}")],
        [InlineKeyboardButton("➕ Добавить карточку", callback_data=f"add_card_{deck_id}")],
        [InlineKeyboardButton("📋 Все карточки", callback_data=f"list_cards_{deck_id}")],
        [InlineKeyboardButton("🗑 Удалить колоду", callback_data=f"delete_deck_{deck_id}")],
        [InlineKeyboardButton("⬅ Назад", callback_data="view_decks")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def start_study_mode(query, user_id, deck_id):
    """Начало режима обучения"""
    cards = db.get_deck_cards(deck_id)
    
    if not cards:
        await query.edit_message_text("В этой колоде нет карточек! Добавьте их сначала. 📝")
        return
    
    random.shuffle(cards)
    
    user_states[user_id] = {
        'mode': 'studying',
        'deck_id': deck_id,
        'cards': cards,
        'current_card_index': 0,
        'correct_count': 0,
        'total_count': len(cards),
        'flipped': False
    }
    
    await show_study_card(query, user_id)

async def show_study_card(query, user_id):
    """Показать текущую карточку"""
    state = user_states.get(user_id, {})
    cards = state.get('cards', [])
    index = state.get('current_card_index', 0)
    
    if index >= len(cards):
        await show_study_results(query, user_id)
        return
    
    card = cards[index]
    is_flipped = state.get('flipped', False)
    progress = f"Карточка {index + 1}/{len(cards)}"
    
    if is_flipped:
        text = f"{progress}\n\n🔄 *ОТВЕТ:*\n\n*{card['answer']}*"
    else:
        text = f"{progress}\n\n❓ *ВОПРОС:*\n\n*{card['question']}*"
    
    keyboard = []
    if not is_flipped:
        keyboard.append([InlineKeyboardButton("🔄 Показать ответ", callback_data="flip_card")])
    else:
        keyboard.append([
            InlineKeyboardButton("❌ Не знаю", callback_data="answer_wrong"),
            InlineKeyboardButton("✅ Знаю", callback_data="answer_correct")
        ])
    keyboard.append([InlineKeyboardButton("⏹ Завершить", callback_data="stop_study")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def show_study_results(query, user_id):
    """Показать результаты обучения"""
    state = user_states.get(user_id, {})
    correct = state.get('correct_count', 0)
    total = state.get('total_count', 0)
    deck_id = state.get('deck_id')
    
    percentage = round((correct / total * 100) if total > 0 else 0, 1)
    db.record_study_session(user_id, deck_id, correct, total)
    
    text = f"""
🎉 *Обучение завершено!*

✅ Правильно: {correct}
❌ Неправильно: {total - correct}
📊 Процент: {percentage}%
    """
    
    keyboard = [
        [InlineKeyboardButton("🔄 Повторить", callback_data=f"study_{deck_id}")],
        [InlineKeyboardButton("📚 Мои колоды", callback_data="view_decks")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    user_states.pop(user_id, None)

async def flip_card(query, user_id):
    """Переворот карточки"""
    state = user_states.get(user_id, {})
    state['flipped'] = not state.get('flipped', False)
    await show_study_card(query, user_id)

async def answer_correct(query, user_id):
    """Правильный ответ"""
    state = user_states.get(user_id, {})
    state['correct_count'] = state.get('correct_count', 0) + 1
    state['current_card_index'] = state.get('current_card_index', 0) + 1
    state['flipped'] = False
    await show_study_card(query, user_id)

async def answer_wrong(query, user_id):
    """Неправильный ответ"""
    state = user_states.get(user_id, {})
    state['current_card_index'] = state.get('current_card_index', 0) + 1
    state['flipped'] = False
    await show_study_card(query, user_id)

async def stop_study(query, user_id):
    """Завершение обучения"""
    await show_study_results(query, user_id)

async def list_cards_callback(query, deck_id):
    """Показать все карточки колоды"""
    cards = db.get_deck_cards(deck_id)
    
    if not cards:
        await query.edit_message_text("В этой колоде пока нет карточек 📝")
        return
    
    text = "📋 *Все карточки:*\n\n"
    keyboard = []
    
    for i, card in enumerate(cards, 1):
        text += f"{i}. ❓ {card['question']}\n   ✏️ {card['answer']}\n\n"
        keyboard.append([InlineKeyboardButton(f"🗑 Удалить #{i}", callback_data=f"delete_card_{card['card_id']}_{deck_id}")])
    
    keyboard.append([InlineKeyboardButton("⬅ Назад", callback_data=f"deck_{deck_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def delete_card_callback(query, user_id, card_id, deck_id):
    """Удаление карточки"""
    db.delete_card(card_id)
    await query.edit_message_text("✅ Карточка удалена! 🗑")
    if deck_id:
        await list_cards_callback(query, deck_id)
    else:
        await view_decks_callback(query, user_id)

async def delete_deck_callback(query, user_id, deck_id):
    """Удаление колоды с подтверждением"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_deck_{deck_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"deck_{deck_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("⚠️ Вы уверены? Это удалит колоду и все карточки!", reply_markup=reply_markup)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    state = user_states.get(user_id, {})
    mode = state.get('mode')
    
    if mode == 'creating_deck':
        deck_id = db.create_deck(user_id, text)
        user_states[user_id] = {'mode': 'adding_cards', 'deck_id': deck_id, 'deck_name': text}
        await update.message.reply_text(
            f"✅ Колода '{text}' создана!\n\n"
            f"Теперь добавляйте карточки.\n"
            f"Формат: *Вопрос | Ответ*\n\n"
            f"Пример: What is 2+2? | 4\n\n"
            f"Введите 'готово' когда закончите."
        )
    
    elif mode == 'adding_cards':
        if text.lower() == 'готово':
            deck_id = state['deck_id']
            deck_info = db.get_deck_info(deck_id)
            text_reply = f"""
✅ *Колода создана успешно!*

📖 {state['deck_name']}
📝 Карточек добавлено: {deck_info['card_count']}

Что дальше?
            """
            keyboard = [
                [InlineKeyboardButton("🎓 Учиться", callback_data=f"study_{deck_id}")],
                [InlineKeyboardButton("➕ Добавить еще", callback_data=f"add_card_{deck_id}")],
                [InlineKeyboardButton("📚 Мои колоды", callback_data="view_decks")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text_reply, reply_markup=reply_markup, parse_mode="Markdown")
            user_states[user_id] = {'mode': 'main'}
        
        elif '|' in text:
            parts = text.split('|')
            if len(parts) == 2:
                question = parts[0].strip()
                answer = parts[1].strip()
                if question and answer:
                    db.add_card(state['deck_id'], question, answer)
                    await update.message.reply_text(
                        f"✅ Карточка добавлена!\n\n❓ {question}\n✏️ {answer}\n\nДобавьте еще или введите 'готово'"
                    )
        else:
            await update.message.reply_text("Неправильный формат! Используйте: *Вопрос | Ответ*")
