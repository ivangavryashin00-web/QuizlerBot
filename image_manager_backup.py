"""
Модуль для работы с картинками в карточках
Поддержка загрузки, сохранения, отображения и поиска картинок
"""

import os
import sqlite3
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
# import requests
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
    """Временно отключено"""
    return None
    # try:
    #     response = requests.get(url, timeout=10)
    #     ... (весь остальной код)
