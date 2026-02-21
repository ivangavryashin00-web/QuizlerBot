"""
Утилиты для QuizletBot
"""

import json
import csv
from datetime import datetime
from typing import List, Dict, Tuple

class CardImporter:
    """Импорт карточек из различных форматов"""
    
    @staticmethod
    def import_from_csv(file_path: str) -> List[Tuple[str, str]]:
        """
        Импорт карточек из CSV файла
        Формат: question,answer
        """
        cards = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file, fieldnames=['question', 'answer'])
                for row in reader:
                    if row['question'] and row['answer']:
                        cards.append((row['question'].strip(), row['answer'].strip()))
        except Exception as e:
            print(f"Ошибка при импорте CSV: {e}")
        
        return cards
    
    @staticmethod
    def import_from_json(file_path: str) -> List[Tuple[str, str]]:
        """
        Импорт карточек из JSON файла
        Формат: [{"question": "q1", "answer": "a1"}, ...]
        """
        cards = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for item in data:
                    if isinstance(item, dict) and 'question' in item and 'answer' in item:
                        cards.append((item['question'].strip(), item['answer'].strip()))
        except Exception as e:
            print(f"Ошибка при импорте JSON: {e}")
        
        return cards
    
    @staticmethod
    def import_from_text(text: str, separator: str = '|') -> List[Tuple[str, str]]:
        """
        Импорт карточек из текста
        Каждая строка - одна карточка в формате: question|answer
        """
        cards = []
        
        for line in text.strip().split('\n'):
            if separator in line:
                parts = line.split(separator)
                if len(parts) >= 2:
                    question = parts[0].strip()
                    answer = parts[1].strip()
                    
                    if question and answer:
                        cards.append((question, answer))
        
        return cards


class CardExporter:
    """Экспорт карточек в различные форматы"""
    
    @staticmethod
    def export_to_csv(cards: List[Dict], file_path: str) -> bool:
        """Экспорт карточек в CSV"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['question', 'answer'])
                writer.writeheader()
                
                for card in cards:
                    writer.writerow({
                        'question': card['question'],
                        'answer': card['answer']
                    })
            
            return True
        except Exception as e:
            print(f"Ошибка при экспорте в CSV: {e}")
            return False
    
    @staticmethod
    def export_to_json(cards: List[Dict], file_path: str) -> bool:
        """Экспорт карточек в JSON"""
        try:
            data = []
            
            for card in cards:
                data.append({
                    'question': card['question'],
                    'answer': card['answer'],
                    'difficulty': card.get('difficulty', 1)
                })
            
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Ошибка при экспорте в JSON: {e}")
            return False
    
    @staticmethod
    def export_to_text(cards: List[Dict], file_path: str) -> bool:
        """Экспорт карточек в текстовый файл"""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                for i, card in enumerate(cards, 1):
                    file.write(f"{i}. {card['question']} | {card['answer']}\n")
            
            return True
        except Exception as e:
            print(f"Ошибка при экспорте в текст: {e}")
            return False


class StatsFormatter:
    """Форматирование статистики для вывода"""
    
    @staticmethod
    def format_accuracy(correct: int, total: int) -> str:
        """Форматирование процента правильных ответов"""
        if total == 0:
            return "0%"
        
        percentage = (correct / total) * 100
        
        if percentage >= 80:
            emoji = "🟢"  # Зеленый
        elif percentage >= 60:
            emoji = "🟡"  # Желтый
        else:
            emoji = "🔴"  # Красный
        
        return f"{emoji} {percentage:.1f}%"
    
    @staticmethod
    def format_time(timestamp: str) -> str:
        """Форматирование времени"""
        if not timestamp:
            return "Никогда"
        
        try:
            dt = datetime.fromisoformat(timestamp)
            now = datetime.now()
            diff = now - dt
            
            if diff.days == 0:
                if diff.seconds < 3600:
                    minutes = diff.seconds // 60
                    return f"{minutes}м назад"
                else:
                    hours = diff.seconds // 3600
                    return f"{hours}ч назад"
            elif diff.days == 1:
                return "Вчера"
            elif diff.days < 7:
                return f"{diff.days}д назад"
            else:
                return dt.strftime('%d.%m.%Y')
        except:
            return timestamp
    
    @staticmethod
    def format_deck_stats(deck_info: Dict, study_stats: Dict) -> str:
        """Полная статистика по колоде"""
        text = f"""
📊 *Статистика по колоде*

📖 Название: {deck_info['name']}
📝 Карточек: {deck_info['card_count']}
📅 Создана: {datetime.fromisoformat(deck_info['created_at']).strftime('%d.%m.%Y')}

📈 Обучение:
   • Сеансов: {study_stats.get('cards_studied', 0)}
   • Правильных ответов: {study_stats.get('correct_answers', 0)}
   • Всего попыток: {study_stats.get('total_attempts', 0)}
   • Точность: {StatsFormatter.format_accuracy(study_stats.get('correct_answers', 0), study_stats.get('total_attempts', 0))}
   • Последний сеанс: {StatsFormatter.format_time(study_stats.get('last_studied'))}
        """
        
        return text.strip()


class TextFormatter:
    """Форматирование текста для Telegram"""
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Экранирование специальных символов Markdown"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    @staticmethod
    def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Обрезание текста до максимальной длины"""
        if len(text) > max_length:
            return text[:max_length - len(suffix)] + suffix
        return text
    
    @staticmethod
    def split_long_message(text: str, max_length: int = 4096) -> List[str]:
        """Разделение длинного сообщения на части"""
        if len(text) <= max_length:
            return [text]
        
        messages = []
        current_message = ""
        
        for line in text.split('\n'):
            if len(current_message) + len(line) + 1 <= max_length:
                current_message += line + '\n'
            else:
                if current_message:
                    messages.append(current_message.rstrip())
                current_message = line + '\n'
        
        if current_message:
            messages.append(current_message.rstrip())
        
        return messages


class DifficultyManager:
    """Управление сложностью карточек"""
    
    DIFFICULTY_LEVELS = {
        1: "Легко 🟢",
        2: "Средне 🟡",
        3: "Сложно 🔴"
    }
    
    @staticmethod
    def get_difficulty_color(level: int) -> str:
        """Получить цвет для уровня сложности"""
        colors = {1: "🟢", 2: "🟡", 3: "🔴"}
        return colors.get(level, "⚪")
    
    @staticmethod
    def calculate_difficulty(correct_answers: int, total_attempts: int) -> int:
        """
        Вычислить сложность карточки на основе результатов
        1 - легко (высокий процент правильных)
        2 - средне
        3 - сложно (низкий процент правильных)
        """
        if total_attempts == 0:
            return 1
        
        accuracy = correct_answers / total_attempts
        
        if accuracy >= 0.7:
            return 1  # Легко
        elif accuracy >= 0.4:
            return 2  # Средне
        else:
            return 3  # Сложно


# Примеры использования:
if __name__ == "__main__":
    # Пример импорта из текста
    text = """What is 2+2? | 4
Hello | Привет
Python | Язык программирования"""
    
    cards = CardImporter.import_from_text(text)
    print("Импортировано карточек:", len(cards))
    for q, a in cards:
        print(f"  {q} -> {a}")
    
    # Пример форматирования текста
    long_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    short = TextFormatter.truncate(long_text, 30)
    print(f"\nОригинал: {long_text}")
    print(f"Обрезано: {short}")
