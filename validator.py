"""
Модуль валидации входных данных для Movie Library.
Возвращает (True, (year, rating)) при успехе или (False, "сообщение") при ошибке.
"""

from __future__ import annotations

MIN_YEAR = 1888   # год первого фильма в истории
MAX_YEAR = 2100


def validate_movie(
    title: str,
    genre: str,
    year_str: str,
    rating_str: str,
) -> tuple[bool, tuple[int, float] | str]:
    """
    Проверяет данные фильма.

    Returns:
        (True, (year: int, rating: float)) — если данные корректны.
        (False, error_message: str)        — если найдена ошибка.
    """
    if not title:
        return False, "Поле «Название» не может быть пустым."

    if not genre:
        return False, "Поле «Жанр» не может быть пустым."

    # --- год ---
    if not year_str:
        return False, "Поле «Год выпуска» не может быть пустым."

    if not year_str.lstrip("-").isdigit():
        return False, "«Год выпуска» должен быть целым числом (например, 2024)."

    year = int(year_str)
    if year < MIN_YEAR or year > MAX_YEAR:
        return False, f"«Год выпуска» должен быть в диапазоне {MIN_YEAR}–{MAX_YEAR}."

    # --- рейтинг ---
    if not rating_str:
        return False, "Поле «Рейтинг» не может быть пустым."

    try:
        rating = float(rating_str.replace(",", "."))
    except ValueError:
        return False, "«Рейтинг» должен быть числом (например, 8.5)."

    if rating < 0 or rating > 10:
        return False, "«Рейтинг» должен быть в диапазоне от 0 до 10."

    return True, (year, round(rating, 1))
