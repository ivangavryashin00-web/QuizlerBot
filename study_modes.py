import random
from difflib import SequenceMatcher
from database import Database

db = Database()

class StudyModes:
    """Режимы обучения"""
    
    @staticmethod
    def prepare_cards(user_id, deck_id, mode='flashcard', limit=20):
        """Подготовить карточки для обучения"""
        cards = db.get_deck_cards(deck_id)
        
        if not cards:
            return []
        
        # Приоритет сложным и новым карточкам
        if mode in ['write', 'quiz']:
            # Сортируем: сначала те, что плохо знаем
            cards.sort(key=lambda x: x.get('difficulty', 1), reverse=True)
        
        # Перемешиваем для разнообразия
        random.shuffle(cards)
        
        return cards[:limit]
    
    @staticmethod
    def calculate_similarity(a, b):
        """Рассчитать схожесть двух строк (0-1)"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    @staticmethod
    def generate_quiz_options(correct_card, all_cards, num_options=4):
        """Сгенерировать варианты ответа для теста"""
        correct_answer = correct_card['answer']
        options = [correct_answer]
        
        # Берем случайные неправильные ответы
        other_cards = [c for c in all_cards if c['card_id'] != correct_card['card_id']]
        wrong_answers = random.sample([c['answer'] for c in other_cards], 
                                     min(num_options-1, len(other_cards)))
        
        options.extend(wrong_answers)
        random.shuffle(options)
        
        return options
    
    @staticmethod
    def get_hint(answer, reveal_percent=0.3):
        """Получить подсказку (часть ответа)"""
        length = len(answer)
        reveal_count = max(1, int(length * reveal_percent))
        
        # Показываем первые буквы
        hint = answer[:reveal_count] + '*' * (length - reveal_count)
        return hint
    
    @staticmethod
    def calculate_next_review(difficulty, correct_streak):
        """Рассчитать следующее время повторения"""
        # Алгоритм интервалов (упрощенный SM-2)
        base_intervals = [1, 3, 7, 14, 30, 60, 120]  # дни
        
        if difficulty > 2:  # Сложное слово
            index = max(0, correct_streak - 2)
        elif difficulty > 1:  # Среднее
            index = correct_streak
        else:  # Легкое
            index = min(correct_streak + 1, len(base_intervals) - 1)
        
        days = base_intervals[min(index, len(base_intervals) - 1)]
        return days
