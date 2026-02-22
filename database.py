import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple, Optional

class Database:
    def __init__(self, db_name='quizlet_bot.db'):
        self.db_name = db_name
    
    def get_connection(self):
        """Получить соединение с БД"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Инициализация таблиц в БД"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица колод карточек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decks (
                deck_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица карточек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                card_id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                difficulty INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deck_id) REFERENCES decks(deck_id)
            )
        ''')
        
        # Таблица статистики обучения
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_stats (
                stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                deck_id INTEGER NOT NULL,
                cards_learned INTEGER DEFAULT 0,
                cards_studied INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                total_attempts INTEGER DEFAULT 0,
                last_studied TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (deck_id) REFERENCES decks(deck_id)
            )
        ''')
        
        # ===== НОВЫЕ ТАБЛИЦЫ =====
        
        # Таблица прогресса карточек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_progress (
                progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                level INTEGER DEFAULT 0,
                next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                correct_count INTEGER DEFAULT 0,
                wrong_count INTEGER DEFAULT 0,
                UNIQUE(user_id, card_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (card_id) REFERENCES cards(card_id)
            )
        ''')
        
        # Таблица геймификации
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_gamification (
                user_id INTEGER PRIMARY KEY,
                total_points INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                last_study_date DATE,
                study_days_streak INTEGER DEFAULT 0,
                achievements TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица настроек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                notifications BOOLEAN DEFAULT 1,
                difficulty TEXT DEFAULT 'medium',
                cards_per_session INTEGER DEFAULT 20,
                reminder_time TEXT DEFAULT '20:00',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ===== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ =====
    def add_user(self, user_id: int, username: str = None):
        """Добавить или обновить пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if cursor.fetchone():
            cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', 
                         (username, user_id))
        else:
            cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)',
                         (user_id, username))
        
        conn.commit()
        conn.close()
    
    # ===== РАБОТА С КОЛОДАМИ =====
    def create_deck(self, user_id: int, name: str, description: str = None) -> int:
        """Создать новую колоду"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO decks (user_id, name, description)
            VALUES (?, ?, ?)
        ''', (user_id, name, description))
        
        deck_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return deck_id
    
    def get_user_decks(self, user_id: int) -> List[Dict]:
        """Получить все колоды пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT d.deck_id, d.name, d.description, 
                   COUNT(c.card_id) as card_count,
                   d.created_at
            FROM decks d
            LEFT JOIN cards c ON d.deck_id = c.deck_id
            WHERE d.user_id = ?
            GROUP BY d.deck_id
            ORDER BY d.updated_at DESC
        ''', (user_id,))
        
        decks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return decks
    
    def delete_deck(self, deck_id: int, user_id: int) -> bool:
        """Удалить колоду"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM decks WHERE deck_id = ?', (deck_id,))
        result = cursor.fetchone()
        
        if not result or result['user_id'] != user_id:
            conn.close()
            return False
        
        cursor.execute('DELETE FROM cards WHERE deck_id = ?', (deck_id,))
        cursor.execute('DELETE FROM learning_stats WHERE deck_id = ?', (deck_id,))
        cursor.execute('DELETE FROM card_progress WHERE deck_id = ?', (deck_id,))
        cursor.execute('DELETE FROM decks WHERE deck_id = ?', (deck_id,))
        
        conn.commit()
        conn.close()
        return True
    
    def get_deck_info(self, deck_id: int) -> Optional[Dict]:
        """Получить информацию о колоде"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT d.*, COUNT(c.card_id) as card_count
            FROM decks d
            LEFT JOIN cards c ON d.deck_id = c.deck_id
            WHERE d.deck_id = ?
            GROUP BY d.deck_id
        ''', (deck_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    # ===== РАБОТА С КАРТОЧКАМИ =====
    def add_card(self, deck_id: int, question: str, answer: str) -> int:
        """Добавить карточку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO cards (deck_id, question, answer)
            VALUES (?, ?, ?)
        ''', (deck_id, question, answer))
        
        card_id = cursor.lastrowid
        
        cursor.execute('UPDATE decks SET updated_at = ? WHERE deck_id = ?',
                      (datetime.now(), deck_id))
        
        conn.commit()
        conn.close()
        
        return card_id
    
    def get_deck_cards(self, deck_id: int) -> List[Dict]:
        """Получить все карточки из колоды"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM cards WHERE deck_id = ? ORDER BY card_id',
                      (deck_id,))
        
        cards = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return cards
    
    def get_card(self, card_id: int) -> Optional[Dict]:
        """Получить информацию о карточке"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM cards WHERE card_id = ?', (card_id,))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def delete_card(self, card_id: int) -> bool:
        """Удалить карточку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cards WHERE card_id = ?', (card_id,))
        cursor.execute('DELETE FROM card_progress WHERE card_id = ?', (card_id,))
        
        conn.commit()
        conn.close()
        return True
    
    def update_card(self, card_id: int, question: str = None, answer: str = None) -> bool:
        """Обновить карточку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if question:
            cursor.execute('UPDATE cards SET question = ?, updated_at = ? WHERE card_id = ?',
                          (question, datetime.now(), card_id))
        
        if answer:
            cursor.execute('UPDATE cards SET answer = ?, updated_at = ? WHERE card_id = ?',
                          (answer, datetime.now(), card_id))
        
        conn.commit()
        conn.close()
        return True
    
    # ===== СТАТИСТИКА =====
    def record_study_session(self, user_id: int, deck_id: int, 
                           correct: int, total: int):
        """Записать результаты обучения"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT stat_id FROM learning_stats 
            WHERE user_id = ? AND deck_id = ?
        ''', (user_id, deck_id))
        
        result = cursor.fetchone()
        
        if result:
            stat_id = result['stat_id']
            cursor.execute('''
                UPDATE learning_stats 
                SET cards_studied = cards_studied + ?,
                    correct_answers = correct_answers + ?,
                    total_attempts = total_attempts + ?,
                    last_studied = ?
                WHERE stat_id = ?
            ''', (1, correct, total, datetime.now(), stat_id))
        else:
            cursor.execute('''
                INSERT INTO learning_stats 
                (user_id, deck_id, cards_studied, correct_answers, total_attempts, last_studied)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, deck_id, 1, correct, total, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Получить статистику пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT deck_id) as decks_count,
                COALESCE(SUM(cards_studied), 0) as total_studied,
                COALESCE(SUM(correct_answers), 0) as total_correct,
                COALESCE(SUM(total_attempts), 0) as total_attempts,
                MAX(last_studied) as last_studied
            FROM learning_stats
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            stats = dict(result)
            stats['accuracy'] = round(
                (stats['total_correct'] / stats['total_attempts'] * 100)
                if stats['total_attempts'] > 0 else 0, 1
            )
            return stats
        
        return {
            'decks_count': 0,
            'total_studied': 0,
            'total_correct': 0,
            'total_attempts': 0,
            'accuracy': 0,
            'last_studied': None
        }
