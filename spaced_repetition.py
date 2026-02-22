from datetime import datetime, timedelta
from database import Database

db = Database()

class SpacedRepetition:
    """Интервальное повторение (SRS)"""
    
    @staticmethod
    def init_card(user_id, card_id):
        """Инициализировать карточку в системе повторения"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO card_progress 
            (user_id, card_id, level, next_review, correct_count, wrong_count)
            VALUES (?, ?, 0, datetime('now'), 0, 0)
        ''', (user_id, card_id))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def update_card_progress(user_id, card_id, result):
        """Обновить прогресс карточки"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Получаем текущий прогресс
        cursor.execute('''
            SELECT level, correct_count, wrong_count 
            FROM card_progress 
            WHERE user_id = ? AND card_id = ?
        ''', (user_id, card_id))
        
        row = cursor.fetchone()
        if not row:
            SpacedRepetition.init_card(user_id, card_id)
            level, correct, wrong = 0, 0, 0
        else:
            level, correct, wrong = row
        
        # Обновляем статистику
        if result == 'correct':
            correct += 1
            level = min(level + 1, 6)  # Максимальный уровень 6
        elif result == 'wrong':
            wrong += 1
            level = max(level - 1, 0)  # Минимальный уровень 0
        elif result == 'again':
            wrong += 1
            level = 0  # Сброс уровня
        
        # Рассчитываем следующее повторение
        intervals = [0, 1, 3, 7, 14, 30, 60]  # дни для каждого уровня
        next_review = datetime.now() + timedelta(days=intervals[level])
        
        cursor.execute('''
            UPDATE card_progress 
            SET level = ?, next_review = ?, correct_count = ?, wrong_count = ?
            WHERE user_id = ? AND card_id = ?
        ''', (level, next_review, correct, wrong, user_id, card_id))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_due_cards(user_id, deck_id):
        """Получить карточки, которые пора повторить"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, cp.level 
            FROM cards c
            JOIN card_progress cp ON c.card_id = cp.card_id
            WHERE c.deck_id = ? AND cp.user_id = ? AND cp.next_review <= datetime('now')
            ORDER BY cp.level ASC
        ''', (deck_id, user_id))
        
        cards = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return cards
    
    @staticmethod
    def get_deck_progress(user_id, deck_id):
        """Получить процент выученности колоды"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN cp.level >= 4 THEN 1 END) as mastered,
                COUNT(*) as total
            FROM cards c
            LEFT JOIN card_progress cp ON c.card_id = cp.card_id AND cp.user_id = ?
            WHERE c.deck_id = ?
        ''', (user_id, deck_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row['total'] > 0:
            return round((row['mastered'] / row['total']) * 100)
        return 0
    
    @staticmethod
    def get_detailed_stats(user_id, deck_id):
        """Детальная статистика по колоде"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN level >= 4 THEN 1 END) as mastered,
                COUNT(CASE WHEN level BETWEEN 1 AND 3 THEN 1 END) as learning,
                COUNT(CASE WHEN level = 0 OR level IS NULL THEN 1 END) as review,
                COUNT(*) as total
            FROM cards c
            LEFT JOIN card_progress cp ON c.card_id = cp.card_id AND cp.user_id = ?
            WHERE c.deck_id = ?
        ''', (user_id, deck_id))
        
        row = cursor.fetchone()
        conn.close()
        
        total = row['total'] or 1
        return {
            'mastered': row['mastered'],
            'learning': row['learning'],
            'review': row['review'],
            'total': row['total'],
            'progress': round((row['mastered'] / total) * 100)
        }
