import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_name='quizlet_bot.db'):
        self.db_name = db_name

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_stats (
                stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                deck_id INTEGER NOT NULL,
                cards_studied INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                total_attempts INTEGER DEFAULT 0,
                last_studied TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (deck_id) REFERENCES decks(deck_id)
            )
        ''')

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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                notifications INTEGER DEFAULT 1,
                difficulty TEXT DEFAULT 'medium',
                cards_per_session INTEGER DEFAULT 20,
                reminder_time TEXT DEFAULT '20:00',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        conn.commit()
        conn.close()

    # ===== ПОЛЬЗОВАТЕЛИ =====

    def add_user(self, user_id: int, username: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if cursor.fetchone():
            cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))
        else:
            cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        conn.commit()
        conn.close()

    # ===== КОЛОДЫ =====

    def create_deck(self, user_id: int, name: str, description: str = None) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO decks (user_id, name, description) VALUES (?, ?, ?)',
            (user_id, name, description)
        )
        deck_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return deck_id

    def get_user_decks(self, user_id: int) -> List[Dict]:
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
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM decks WHERE deck_id = ?', (deck_id,))
        result = cursor.fetchone()
        if not result or result['user_id'] != user_id:
            conn.close()
            return False
        # Delete card_progress for all cards in deck
        cursor.execute(
            'DELETE FROM card_progress WHERE card_id IN (SELECT card_id FROM cards WHERE deck_id = ?)',
            (deck_id,)
        )
        cursor.execute('DELETE FROM cards WHERE deck_id = ?', (deck_id,))
        cursor.execute('DELETE FROM learning_stats WHERE deck_id = ?', (deck_id,))
        cursor.execute('DELETE FROM decks WHERE deck_id = ?', (deck_id,))
        conn.commit()
        conn.close()
        return True

    def get_deck_info(self, deck_id: int) -> Optional[Dict]:
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

    # ===== КАРТОЧКИ =====

    def add_card(self, deck_id: int, question: str, answer: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO cards (deck_id, question, answer) VALUES (?, ?, ?)',
            (deck_id, question, answer)
        )
        card_id = cursor.lastrowid
        cursor.execute('UPDATE decks SET updated_at = ? WHERE deck_id = ?', (datetime.now(), deck_id))
        conn.commit()
        conn.close()
        return card_id

    def get_deck_cards(self, deck_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards WHERE deck_id = ? ORDER BY card_id', (deck_id,))
        cards = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return cards

    def get_card(self, card_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards WHERE card_id = ?', (card_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def delete_card(self, card_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM card_progress WHERE card_id = ?', (card_id,))
        cursor.execute('DELETE FROM cards WHERE card_id = ?', (card_id,))
        conn.commit()
        conn.close()
        return True

    def update_card(self, card_id: int, question: str = None, answer: str = None) -> bool:
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

    def record_study_session(self, user_id: int, deck_id: int, correct: int, total: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT stat_id FROM learning_stats WHERE user_id = ? AND deck_id = ?',
            (user_id, deck_id)
        )
        result = cursor.fetchone()
        if result:
            cursor.execute('''
                UPDATE learning_stats
                SET cards_studied = cards_studied + 1,
                    correct_answers = correct_answers + ?,
                    total_attempts = total_attempts + ?,
                    last_studied = ?
                WHERE user_id = ? AND deck_id = ?
            ''', (correct, total, datetime.now(), user_id, deck_id))
        else:
            cursor.execute('''
                INSERT INTO learning_stats
                (user_id, deck_id, cards_studied, correct_answers, total_attempts, last_studied)
                VALUES (?, ?, 1, ?, ?, ?)
            ''', (user_id, deck_id, correct, total, datetime.now()))
        conn.commit()
        conn.close()

    def get_user_stats(self, user_id: int) -> Dict:
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
            # Also count decks created
            conn2 = self.get_connection()
            c2 = conn2.cursor()
            c2.execute('SELECT COUNT(*) as cnt FROM decks WHERE user_id = ?', (user_id,))
            r2 = c2.fetchone()
            conn2.close()
            stats['decks_count'] = r2['cnt'] if r2 else 0
            return stats
        return {
            'decks_count': 0, 'total_studied': 0, 'total_correct': 0,
            'total_attempts': 0, 'accuracy': 0, 'last_studied': None
        }

    # ===== НАСТРОЙКИ =====

    def get_user_settings(self, user_id: int) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return dict(result)
        # Create default settings
        self._init_user_settings(user_id)
        return {
            'user_id': user_id,
            'notifications': 1,
            'difficulty': 'medium',
            'cards_per_session': 20,
            'reminder_time': '20:00'
        }

    def _init_user_settings(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)',
            (user_id,)
        )
        conn.commit()
        conn.close()

    def update_user_setting(self, user_id: int, key: str, value) -> bool:
        allowed = {'notifications', 'difficulty', 'cards_per_session', 'reminder_time'}
        if key not in allowed:
            return False
        self._init_user_settings(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE user_settings SET {key} = ? WHERE user_id = ?',
            (value, user_id)
        )
        conn.commit()
        conn.close()
        return True
