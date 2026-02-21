"""
🤖 Полная интеграция с Anthropic Claude API для QuizletBot

Функции:
- Генерирование примеров использования слов
- Генерирование определений и объяснений
- Проверка правильности ответов
- Создание контрольных вопросов
- Адаптивное обучение
"""

import os
import asyncio
from typing import Optional, List, Dict
from anthropic import Anthropic, AsyncAnthropic
from functools import lru_cache
import json
from datetime import datetime

class AIAssistant:
    """Основной класс для работы с Claude AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация AI ассистента
        
        Args:
            api_key: Anthropic API ключ (если None, берется из ANTHROPIC_API_KEY)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "❌ ANTHROPIC_API_KEY не установлена!\n"
                "Установите переменную окружения ANTHROPIC_API_KEY"
            )
        
        self.client = Anthropic(api_key=self.api_key)
        self.async_client = AsyncAnthropic(api_key=self.api_key)
        self.model = "claude-opus-4-5-20251101"
        self.max_tokens = 500
        self.conversation_history = {}
    
    def generate_definition(self, word: str, language: str = "ru") -> str:
        """
        Генерирование определения слова
        
        Args:
            word: Слово для определения
            language: Язык ответа
            
        Returns:
            Определение слова
            
        Example:
            >>> ai = AIAssistant()
            >>> definition = ai.generate_definition("photosynthesis")
            >>> print(definition)
            "Процесс преобразования света в химическую энергию..."
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": f"Дай краткое определение (2-3 предложения) для слова '{word}' на {language}. Определение должно быть простым и понятным."
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            print(f"❌ Ошибка при генерировании определения: {e}")
            return f"Не удалось сгенерировать определение для '{word}'"
    
    def generate_examples(self, word: str, count: int = 3, language: str = "ru") -> List[str]:
        """
        Генерирование примеров использования слова
        
        Args:
            word: Слово для примеров
            count: Количество примеров
            language: Язык примеров
            
        Returns:
            Список примеров
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": f"Напиши {count} примера использования слова '{word}' в предложениях на {language}. Каждый пример на отдельной строке, начинай с номера (1., 2., и т.д.)"
                    }
                ]
            )
            
            text = message.content[0].text
            examples = [line.strip() for line in text.split('\n') if line.strip()]
            
            return examples[:count]
            
        except Exception as e:
            print(f"❌ Ошибка при генерировании примеров: {e}")
            return []
    
    def check_answer(self, question: str, user_answer: str, correct_answer: str, explain: bool = True) -> Dict:
        """
        Проверка правильности ответа с объяснением
        
        Args:
            question: Вопрос
            user_answer: Ответ пользователя
            correct_answer: Правильный ответ
            explain: Давать ли объяснение
            
        Returns:
            Словарь с результатом проверки
            
        Example:
            >>> result = ai.check_answer(
            ...     "Столица Франции?",
            ...     "Лион",
            ...     "Париж"
            ... )
            >>> print(result['is_correct'])  # False
            >>> print(result['feedback'])  # "Лион - это второй крупнейший город..."
        """
        try:
            prompt = f"""Проверь ответ пользователя:

Вопрос: {question}
Ответ пользователя: {user_answer}
Правильный ответ: {correct_answer}

Определи:
1. Правильный ли ответ (yes/no)
2. Объяснение почему (если объяснение нужно)
3. Оценка из 10 (насколько близко к правильному ответу)

Формат ответа:
CORRECT: yes/no
SCORE: число
EXPLANATION: текст (если explain=True)"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = message.content[0].text
            
            # Парсим ответ
            lines = response_text.split('\n')
            result = {
                "is_correct": "yes" in lines[0].lower(),
                "score": 0,
                "feedback": "",
                "full_response": response_text
            }
            
            for line in lines:
                if "SCORE:" in line:
                    try:
                        result["score"] = int(line.split(":")[-1].strip())
                    except:
                        pass
                if "EXPLANATION:" in line:
                    result["feedback"] = line.split(":")[-1].strip()
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка при проверке ответа: {e}")
            return {
                "is_correct": False,
                "score": 0,
                "feedback": "Ошибка при проверке",
                "full_response": str(e)
            }
    
    def generate_test_questions(self, topic: str, count: int = 5, difficulty: str = "medium") -> List[Dict]:
        """
        Генерирование контрольных вопросов по теме
        
        Args:
            topic: Тема для вопросов
            count: Количество вопросов
            difficulty: Сложность (easy, medium, hard)
            
        Returns:
            Список вопросов с ответами
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Напиши {count} контрольных вопросов по теме '{topic}' с уровнем сложности '{difficulty}'.

Формат JSON:
[
  {{
    "question": "вопрос",
    "answer": "ответ",
    "explanation": "объяснение"
  }},
  ...
]

Возвращай ТОЛЬКО JSON без дополнительного текста."""
                    }
                ]
            )
            
            text = message.content[0].text
            # Парсим JSON
            questions = json.loads(text)
            
            return questions
            
        except Exception as e:
            print(f"❌ Ошибка при генерировании вопросов: {e}")
            return []
    
    async def generate_definition_async(self, word: str, language: str = "ru") -> str:
        """Асинхронное генерирование определения"""
        try:
            message = await self.async_client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": f"Дай краткое определение для слова '{word}' на {language}."
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return f"Ошибка при обработке '{word}'"
    
    def create_learning_plan(self, topic: str, level: str = "beginner", days: int = 7) -> str:
        """
        Создание плана обучения
        
        Args:
            topic: Тема обучения
            level: Уровень (beginner, intermediate, advanced)
            days: Количество дней
            
        Returns:
            План обучения
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Создай детальный план обучения по теме '{topic}' для уровня '{level}' на {days} дней.

План должен быть:
- Структурированным
- С конкретными целями на каждый день
- С примерами упражнений
- С советами для быстрого запоминания"""
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            print(f"❌ Ошибка при создании плана: {e}")
            return "Не удалось создать план"
    
    def get_conversation_context(self, user_id: int) -> List[Dict]:
        """Получить историю разговора пользователя"""
        return self.conversation_history.get(user_id, [])
    
    def add_conversation_message(self, user_id: int, role: str, content: str):
        """Добавить сообщение в историю разговора"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Сохраняем только последние 10 сообщений
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
    
    def chat_with_ai(self, user_id: int, message: str) -> str:
        """
        Чат с AI с сохранением контекста разговора
        
        Args:
            user_id: ID пользователя
            message: Сообщение пользователя
            
        Returns:
            Ответ от AI
        """
        try:
            # Добавляем сообщение пользователя в историю
            self.add_conversation_message(user_id, "user", message)
            
            # Получаем историю
            history = self.get_conversation_context(user_id)
            
            # Создаем запрос с историей
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system="Ты полезный помощник для изучения и запоминания информации. Помогай пользователю учиться эффективно.",
                messages=history
            )
            
            answer = response.content[0].text
            
            # Добавляем ответ в историю
            self.add_conversation_message(user_id, "assistant", answer)
            
            return answer
            
        except Exception as e:
            print(f"❌ Ошибка в чате: {e}")
            return f"Ошибка: {str(e)}"
    
    @lru_cache(maxsize=128)
    def translate_word(self, word: str, source_lang: str = "en", target_lang: str = "ru") -> str:
        """Перевод слова"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": f"Переведи слово '{word}' с {source_lang} на {target_lang}. Напиши ТОЛЬКО перевод, без объяснений."
                    }
                ]
            )
            
            return message.content[0].text.strip()
            
        except Exception as e:
            return f"Ошибка: {e}"


class AIFeatures:
    """Дополнительные AI функции"""
    
    def __init__(self, ai_assistant: AIAssistant):
        self.ai = ai_assistant
    
    def suggest_next_card(self, completed_cards: List[str], user_level: str = "intermediate") -> str:
        """Рекомендация следующей карточки"""
        cards_text = ", ".join(completed_cards[-5:])  # Последние 5 карточек
        
        message = self.ai.client.messages.create(
            model=self.ai.model,
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": f"На основе уже пройденных тем: {cards_text}\nКакую тему рекомендуешь изучить следующей для уровня '{user_level}'? Дай короткую рекомендацию."
                }
            ]
        )
        
        return message.content[0].text
    
    def analyze_learning_progress(self, stats: Dict) -> str:
        """Анализ прогресса обучения"""
        stats_text = json.dumps(stats, indent=2, ensure_ascii=False)
        
        message = self.ai.client.messages.create(
            model=self.ai.model,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": f"""Проанализируй мой прогресс обучения и дай рекомендации для улучшения:

Статистика:
{stats_text}

Дай:
1. Оценку текущего прогресса
2. Сильные стороны
3. Области для улучшения
4. Конкретные рекомендации"""
                }
            ]
        )
        
        return message.content[0].text


# Примеры использования
if __name__ == "__main__":
    # Инициализация
    ai = AIAssistant()
    
    print("🤖 QuizletBot AI Assistant\n")
    
    # Пример 1: Генерирование определения
    print("📚 Пример 1: Определение слова")
    definition = ai.generate_definition("photosynthesis")
    print(f"Definition: {definition}\n")
    
    # Пример 2: Примеры использования
    print("📚 Пример 2: Примеры использования")
    examples = ai.generate_examples("serendipity", count=2)
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")
    print()
    
    # Пример 3: Проверка ответа
    print("📚 Пример 3: Проверка ответа")
    result = ai.check_answer(
        "What is 2+2?",
        "5",
        "4"
    )
    print(f"Correct: {result['is_correct']}")
    print(f"Score: {result['score']}/10")
    print(f"Feedback: {result['feedback']}\n")
    
    # Пример 4: Генерирование вопросов
    print("📚 Пример 4: Генерирование контрольных вопросов")
    questions = ai.generate_test_questions("Python Programming", count=3, difficulty="easy")
    for q in questions:
        print(f"Q: {q['question']}")
        print(f"A: {q['answer']}\n")
    
    # Пример 5: План обучения
    print("📚 Пример 5: План обучения")
    plan = ai.create_learning_plan("English Grammar", level="beginner", days=7)
    print(plan)
