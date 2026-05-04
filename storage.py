"""
Модуль сохранения и загрузки данных фильмов в формате JSON.
"""

from __future__ import annotations
import json
import os

DATA_FILE = "movies.json"


def load_movies(path: str = DATA_FILE) -> list[dict]:
    """Загружает список фильмов из JSON-файла. Возвращает [] если файл отсутствует."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_movies(movies: list[dict], path: str = DATA_FILE) -> None:
    """Сохраняет список фильмов в JSON-файл с красивым форматированием."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)
