from datetime import datetime, timedelta
from database import Database

db = Database()

class Gamification:
    """Игровые механики"""
    
    POINTS = {
        'correct_flashcard': 5,
        'correct_write': 10,
        'correct_quiz': 8,
        'streak_bonus': 2,  # множитель за серию
        'perfect_session': 50,  # идеальная сессия
        'daily_study': 20  # ежедневное обучение
    }
    
    ACHIEVEMENTS = {
        'first_steps': {'name': '🌱 Первые шаги', 'desc': 'Выучите первую карточку', 'points': 10},
        'ten_cards': {'name': '🔟 Десятка', 'desc': 'Выучите 10 карточек', 'points': 50},
        'hundred_cards': {'name': '💯 Сотня', 'desc': 'Выучите 100 карточек', 'points': 200},
        'week_streak': {'name': '🔥 Недельная серия', 'desc': 'Учитесь 7 дней подряд', 'points': 100},
        'month_streak': {'name': '📅 Месячная серия', 'desc': 'Учитесь 30 дней подряд', 'points': 500},
        'perfect_quiz': {'name': '🎯 Идеальный тест', 'desc': 'Пройдите тест на 100%', 'points': 50},
        'speed_demon': {'name': '⚡ Скорость', 'desc': 'Выучите 20 карточек за 5 минут', 'points': 100},
        'collector': {'name': '📚 Коллекционер', 'desc': 'Создайте 5 колод', 'points': 50}
    }
    
    @staticmethod
    def init_user(user_id):
        """Инициализировать пользователя"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO user_gamification 
            (user_id, total_points, current_streak, max_streak, last_study_date, study_days_streak)
            VALUES (?, 0, 0, 0, NULL, 0)
        ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def add_points(user_id, action):
        """Добавить очки"""
        points = Gamification.POINTS.get(action, 5)
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_gamification 
            SET total_points = total_points + ?
            WHERE user_id = ?
        ''', (points, user_id))
        
        conn.commit()
        conn.close()
        
        return points
    
    @staticmethod
    def update_streak(user_id):
        """Обновить серию"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT last_study_date, current_streak, study_days_streak 
            FROM user_gamification 
            WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        today = datetime.now().date()
        
        if row['last_study_date']:
            last_date = datetime.strptime(row['last_study_date'], '%Y-%m-%d').date()
            days_diff = (today - last_date).days
            
            if days_diff == 0:  # Уже учились сегодня
                current_streak = row['current_streak']
            elif days_diff == 1:  # Учились вчера - продолжаем серию
                current_streak = row['current_streak'] + 1
            else:  # Пропустили день - сброс
                current_streak = 1
        else:
            current_streak = 1
            study_days = 1
        
        # Обновляем рекорд
        max_streak = max(row['max_streak'], current_streak)
        study_days = row['study_days_streak'] + 1 if row['last_study_date'] != str(today) else row['study_days_streak']
        
        cursor.execute('''
            UPDATE user_gamification 
            SET current_streak = ?, max_streak = ?, last_study_date = ?, study_days_streak = ?
            WHERE user_id = ?
        ''', (current_streak, max_streak, str(today), study_days, user_id))
        
        conn.commit()
        conn.close()
        
        return current_streak
    
    @staticmethod
    def check_achievements(user_id):
        """Проверить достижения"""
        # Логика проверки достижений
        pass
    
    @staticmethod
    def get_full_stats(user_id):
        """Полная статистика"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM user_gamification WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            Gamification.init_user(user_id)
            return {
                'total_points': 0,
                'current_streak': 0,
                'max_streak': 0,
                'study_days_streak': 0,
                'mastered_cards': 0,
                'learning_cards': 0
            }
        
        # Получаем количество карточек
        cursor = db.get_connection().cursor()
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN level >= 4 THEN 1 END) as mastered,
                COUNT(CASE WHEN level < 4 THEN 1 END) as learning
            FROM card_progress 
            WHERE user_id = ?
        ''', (user_id,))
        
        cards = cursor.fetchone()
        
        return {
            'total_points': row['total_points'],
            'current_streak': row['current_streak'],
            'max_streak': row['max_streak'],
            'study_days_streak': row['study_days_streak'],
            'mastered_cards': cards['mastered'] if cards else 0,
            'learning_cards': cards['learning'] if cards else 0
        }
