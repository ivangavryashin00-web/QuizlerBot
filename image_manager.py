"""
Модуль для работы с картинками в карточках
Поддержка загрузки, сохранения, отображения и поиска картинок
"""

import os
import sqlite3
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
import requests
from PIL import Image
from io import BytesIO

class ImageManager:
    """Менеджер для работы с картинками"""
    
    def __init__(self, storage_path: str = "./card_images", max_size_mb: int = 5):
        """
        Инициализация менеджера картинок
        
        Args:
            storage_path: Путь для хранения картинок
            max_size_mb: Максимальный размер файла в МБ
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size_mb * 1024 * 1024
    
    def save_image_from_url(self, url: str, card_id: int) -> Optional[str]:
        """
        Сохранить картинку по URL
        
        Args:
            url: URL картинки
            card_id: ID карточки
            
        Returns:
            Путь к сохраненной картинке или None
        """
        try:
            # Скачивание картинки
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Проверка размера
            if len(response.content) > self.max_size:
                print(f"Картинка слишком большая: {len(response.content)}")
                return None
            
            # Открытие как изображение
            img = Image.open(BytesIO(response.content))
            
            # Оптимизация размера
            img.thumbnail((500, 500), Image.Resampling.LANCZOS)
            
            # Сохранение
            filename = f"card_{card_id}_{datetime.now().timestamp()}.jpg"
            filepath = self.storage_path / filename
            
            img.save(filepath, "JPEG", quality=85)
            
            return str(filepath)
        
        except Exception as e:
            print(f"Ошибка при сохранении картинки: {e}")
            return None
    
    def save_image_from_file(self, file_path: str, card_id: int) -> Optional[str]:
        """
        Сохранить картинку из файла
        
        Args:
            file_path: Путь к файлу
            card_id: ID карточки
            
        Returns:
            Путь к сохраненной картинке
        """
        try:
            if not os.path.exists(file_path):
                print(f"Файл не найден: {file_path}")
                return None
            
            # Проверка размера
            file_size = os.path.getsize(file_path)
            if file_size > self.max_size:
                print(f"Файл слишком большой: {file_size}")
                return None
            
            # Открытие и оптимизация
            img = Image.open(file_path)
            img.thumbnail((500, 500), Image.Resampling.LANCZOS)
            
            # Сохранение
            filename = f"card_{card_id}_{datetime.now().timestamp()}.jpg"
            filepath = self.storage_path / filename
            
            img.save(filepath, "JPEG", quality=85)
            
            return str(filepath)
        
        except Exception as e:
            print(f"Ошибка при сохранении картинки: {e}")
            return None
    
    def delete_image(self, image_path: str) -> bool:
        """
        Удалить картинку
        
        Args:
            image_path: Путь к картинке
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                return True
            return False
        except Exception as e:
            print(f"Ошибка при удалении картинки: {e}")
            return False
    
    def get_image_info(self, image_path: str) -> Optional[Dict]:
        """
        Получить информацию о картинке
        
        Args:
            image_path: Путь к картинке
            
        Returns:
            {'width': int, 'height': int, 'size_kb': float, 'format': str}
        """
        try:
            if not os.path.exists(image_path):
                return None
            
            img = Image.open(image_path)
            file_size = os.path.getsize(image_path) / 1024  # в КБ
            
            return {
                'width': img.width,
                'height': img.height,
                'size_kb': round(file_size, 2),
                'format': img.format
            }
        except Exception as e:
            print(f"Ошибка при получении информации: {e}")
            return None
    
    def optimize_image(self, image_path: str, quality: int = 85, 
                      max_width: int = 500) -> bool:
        """
        Оптимизировать картинку
        
        Args:
            image_path: Путь к картинке
            quality: Качество JPEG (1-100)
            max_width: Максимальная ширина
            
        Returns:
            True если успешно
        """
        try:
            if not os.path.exists(image_path):
                return False
            
            img = Image.open(image_path)
            img.thumbnail((max_width, max_width), Image.Resampling.LANCZOS)
            img.save(image_path, "JPEG", quality=quality, optimize=True)
            
            return True
        except Exception as e:
            print(f"Ошибка при оптимизации: {e}")
            return False


class ImageSearch:
    """Поиск картинок по теме"""
    
    @staticmethod
    def search_images(query: str, limit: int = 5, source: str = "pexels") -> List[str]:
        """
        Поиск картинок по теме
        
        Args:
            query: Тема для поиска
            limit: Количество результатов
            source: Источник (pexels, unsplash, pixabay)
            
        Returns:
            Список URL картинок
        """
        if source == "pexels":
            return ImageSearch._search_pexels(query, limit)
        elif source == "unsplash":
            return ImageSearch._search_unsplash(query, limit)
        else:
            return []
    
    @staticmethod
    def _search_pexels(query: str, limit: int) -> List[str]:
        """Поиск в Pexels (требует API ключ)"""
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            print("PEXELS_API_KEY не установлен")
            return []
        
        try:
            url = "https://api.pexels.com/v1/search"
            params = {
                "query": query,
                "per_page": limit,
                "page": 1
            }
            headers = {"Authorization": api_key}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            images = []
            for photo in data.get("photos", []):
                images.append(photo["src"]["medium"])
            
            return images
        
        except Exception as e:
            print(f"Ошибка при поиске в Pexels: {e}")
            return []
    
    @staticmethod
    def _search_unsplash(query: str, limit: int) -> List[str]:
        """Поиск в Unsplash (требует API ключ)"""
        api_key = os.getenv("UNSPLASH_API_KEY")
        if not api_key:
            print("UNSPLASH_API_KEY не установлен")
            return []
        
        try:
            url = "https://api.unsplash.com/search/photos"
            params = {
                "query": query,
                "per_page": limit,
                "client_id": api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            images = []
            for result in data.get("results", []):
                images.append(result["urls"]["small"])
            
            return images
        
        except Exception as e:
            print(f"Ошибка при поиске в Unsplash: {e}")
            return []


class CardImageDatabase:
    """Хранение связей между карточками и картинками в БД"""
    
    def __init__(self, db_path: str = "quizlet_bot.db"):
        self.db_path = db_path
        self.init_tables()
    
    def init_tables(self):
        """Инициализация таблиц для картинок"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (card_id) REFERENCES cards(card_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_image_to_card(self, card_id: int, image_path: str, 
                         source: str = "uploaded") -> bool:
        """
        Добавить картинку к карточке
        
        Args:
            card_id: ID карточки
            image_path: Путь к картинке
            source: Источник (uploaded, url, search)
            
        Returns:
            True если успешно
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO card_images (card_id, image_path, source)
                VALUES (?, ?, ?)
            ''', (card_id, image_path, source))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при добавлении картинки: {e}")
            return False
    
    def get_card_image(self, card_id: int) -> Optional[str]:
        """
        Получить картинку карточки
        
        Args:
            card_id: ID карточки
            
        Returns:
            Путь к картинке или None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT image_path FROM card_images WHERE card_id = ? ORDER BY created_at DESC LIMIT 1',
                (card_id,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
        except Exception as e:
            print(f"Ошибка при получении картинки: {e}")
            return None
    
    def delete_card_image(self, card_id: int) -> bool:
        """
        Удалить картинку карточки
        
        Args:
            card_id: ID карточки
            
        Returns:
            True если успешно
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM card_images WHERE card_id = ?', (card_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при удалении картинки: {e}")
            return False
    
    def get_all_card_images(self, deck_id: int) -> List[Dict]:
        """
        Получить все картинки колоды
        
        Args:
            deck_id: ID колоды
            
        Returns:
            Список картинок
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ci.image_id, ci.card_id, ci.image_path, ci.source, ci.created_at
                FROM card_images ci
                JOIN cards c ON ci.card_id = c.card_id
                WHERE c.deck_id = ?
            ''', (deck_id,))
            
            results = [dict(zip([d[0] for d in cursor.description], row)) 
                      for row in cursor.fetchall()]
            
            conn.close()
            return results
        except Exception as e:
            print(f"Ошибка при получении картинок: {e}")
            return []


# Примеры использования
if __name__ == "__main__":
    print("=== Примеры работы с картинками ===\n")
    
    # Инициализация менеджера
    img_manager = ImageManager()
    
    # 1. Сохранение картинки с URL
    image_path = img_manager.save_image_from_url(
        "https://example.com/image.jpg",
        card_id=1
    )
    print(f"Сохраненная картинка: {image_path}\n")
    
    # 2. Получить информацию о картинке
    if image_path:
        info = img_manager.get_image_info(image_path)
        print(f"Информация о картинке: {info}\n")
    
    # 3. Поиск картинок
    images = ImageSearch.search_images("cat", limit=5)
    print(f"Найденные картинки: {images}\n")
    
    # 4. Работа с БД картинок
    db = CardImageDatabase()
    if image_path:
        db.add_image_to_card(1, image_path, "uploaded")
        retrieved = db.get_card_image(1)
        print(f"Картинка из БД: {retrieved}\n")
