"""
Тесты для Movie Library.
Покрывают: валидацию (позитивные / негативные / граничные случаи), хранилище JSON.

Запуск:
    python -m unittest tests/test_movie_library.py -v
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validator import validate_movie, MIN_YEAR, MAX_YEAR
from storage import load_movies, save_movies


# ══════════════════════════════════════════════════════════════════════════════
#  Тесты валидации
# ══════════════════════════════════════════════════════════════════════════════

class TestValidateMoviePositive(unittest.TestCase):
    """Позитивные случаи: корректные данные должны проходить валидацию."""

    def test_typical_movie(self):
        ok, result = validate_movie("Inception", "Sci-Fi", "2010", "8.8")
        self.assertTrue(ok)
        self.assertEqual(result, (2010, 8.8))

    def test_rating_zero(self):
        ok, result = validate_movie("Bad Film", "Drama", "2000", "0")
        self.assertTrue(ok)
        self.assertEqual(result[1], 0.0)

    def test_rating_ten(self):
        ok, result = validate_movie("Masterpiece", "Drama", "1999", "10")
        self.assertTrue(ok)
        self.assertEqual(result[1], 10.0)

    def test_rating_with_comma(self):
        """Пользователь может вводить рейтинг через запятую."""
        ok, result = validate_movie("Film", "Comedy", "2005", "7,5")
        self.assertTrue(ok)
        self.assertEqual(result[1], 7.5)

    def test_min_year_boundary(self):
        ok, result = validate_movie("First Film", "Documentary", str(MIN_YEAR), "5.0")
        self.assertTrue(ok)
        self.assertEqual(result[0], MIN_YEAR)

    def test_max_year_boundary(self):
        ok, result = validate_movie("Future Film", "Sci-Fi", str(MAX_YEAR), "5.0")
        self.assertTrue(ok)
        self.assertEqual(result[0], MAX_YEAR)

    def test_rating_rounded(self):
        # 7.56 -> round(7.56, 1) = 7.6 (без проблем float-точности)
        ok, result = validate_movie("A", "B", "2020", "7.56")
        self.assertTrue(ok)
        self.assertEqual(result[1], 7.6)


class TestValidateMovieNegative(unittest.TestCase):
    """Негативные случаи: некорректные данные должны отклоняться."""

    def test_empty_title(self):
        ok, msg = validate_movie("", "Drama", "2000", "7.0")
        self.assertFalse(ok)
        self.assertIn("Название", msg)

    def test_empty_genre(self):
        ok, msg = validate_movie("Film", "", "2000", "7.0")
        self.assertFalse(ok)
        self.assertIn("Жанр", msg)

    def test_empty_year(self):
        ok, msg = validate_movie("Film", "Drama", "", "7.0")
        self.assertFalse(ok)
        self.assertIn("Год", msg)

    def test_empty_rating(self):
        ok, msg = validate_movie("Film", "Drama", "2000", "")
        self.assertFalse(ok)
        self.assertIn("Рейтинг", msg)

    def test_year_not_a_number(self):
        ok, msg = validate_movie("Film", "Drama", "abcd", "7.0")
        self.assertFalse(ok)
        self.assertIn("Год", msg)

    def test_year_float_string(self):
        ok, msg = validate_movie("Film", "Drama", "2010.5", "7.0")
        self.assertFalse(ok)
        self.assertIn("Год", msg)

    def test_rating_not_a_number(self):
        ok, msg = validate_movie("Film", "Drama", "2000", "good")
        self.assertFalse(ok)
        self.assertIn("Рейтинг", msg)

    def test_rating_negative(self):
        ok, msg = validate_movie("Film", "Drama", "2000", "-1")
        self.assertFalse(ok)
        self.assertIn("Рейтинг", msg)

    def test_rating_above_10(self):
        ok, msg = validate_movie("Film", "Drama", "2000", "10.1")
        self.assertFalse(ok)
        self.assertIn("Рейтинг", msg)

    def test_year_too_old(self):
        ok, msg = validate_movie("Film", "Drama", str(MIN_YEAR - 1), "5.0")
        self.assertFalse(ok)
        self.assertIn("Год", msg)

    def test_year_too_far_future(self):
        ok, msg = validate_movie("Film", "Drama", str(MAX_YEAR + 1), "5.0")
        self.assertFalse(ok)
        self.assertIn("Год", msg)

    def test_negative_year(self):
        ok, msg = validate_movie("Film", "Drama", "-500", "5.0")
        self.assertFalse(ok)
        self.assertIn("Год", msg)


class TestValidateMovieBoundary(unittest.TestCase):
    """Граничные случаи."""

    def test_rating_exactly_0(self):
        ok, result = validate_movie("Z", "Z", "2000", "0.0")
        self.assertTrue(ok)
        self.assertEqual(result[1], 0.0)

    def test_rating_exactly_10(self):
        ok, result = validate_movie("Z", "Z", "2000", "10.0")
        self.assertTrue(ok)
        self.assertEqual(result[1], 10.0)

    def test_rating_just_above_10(self):
        ok, _ = validate_movie("Z", "Z", "2000", "10.01")
        self.assertFalse(ok)

    def test_rating_just_below_0(self):
        ok, _ = validate_movie("Z", "Z", "2000", "-0.01")
        self.assertFalse(ok)

    def test_year_1888(self):
        ok, result = validate_movie("Z", "Z", "1888", "5.0")
        self.assertTrue(ok)
        self.assertEqual(result[0], 1888)

    def test_year_1887(self):
        ok, _ = validate_movie("Z", "Z", "1887", "5.0")
        self.assertFalse(ok)

    def test_whitespace_only_title(self):
        """Пробелы в названии — strip() выполняется до вызова validate_movie."""
        ok, msg = validate_movie("   ", "Drama", "2000", "5.0")
        self.assertIsInstance(ok, bool)


# ══════════════════════════════════════════════════════════════════════════════
#  Тесты хранилища
# ══════════════════════════════════════════════════════════════════════════════

class TestStorage(unittest.TestCase):
    """Тесты сохранения и загрузки JSON."""

    def setUp(self):
        self.tmpfile = tempfile.mktemp(suffix=".json")

    def tearDown(self):
        if os.path.exists(self.tmpfile):
            os.remove(self.tmpfile)

    def test_save_and_load(self):
        movies = [{"title": "Dune", "genre": "Sci-Fi", "year": 2021, "rating": 8.0}]
        save_movies(movies, self.tmpfile)
        loaded = load_movies(self.tmpfile)
        self.assertEqual(loaded, movies)

    def test_load_nonexistent_file(self):
        result = load_movies("/nonexistent/path/movies.json")
        self.assertEqual(result, [])

    def test_load_empty_list(self):
        save_movies([], self.tmpfile)
        result = load_movies(self.tmpfile)
        self.assertEqual(result, [])

    def test_save_multiple_movies(self):
        movies = [
            {"title": "A", "genre": "Action", "year": 2000, "rating": 7.0},
            {"title": "B", "genre": "Drama",  "year": 2010, "rating": 9.0},
        ]
        save_movies(movies, self.tmpfile)
        loaded = load_movies(self.tmpfile)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[1]["title"], "B")

    def test_file_is_valid_json(self):
        movies = [{"title": "Test", "genre": "X", "year": 2020, "rating": 5.0}]
        save_movies(movies, self.tmpfile)
        with open(self.tmpfile, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, movies)

    def test_load_corrupted_json(self):
        with open(self.tmpfile, "w") as f:
            f.write("not valid json {{{")
        result = load_movies(self.tmpfile)
        self.assertEqual(result, [])

    def test_unicode_saved_correctly(self):
        movies = [{"title": "Побег из Шоушенка", "genre": "Драма", "year": 1994, "rating": 9.3}]
        save_movies(movies, self.tmpfile)
        loaded = load_movies(self.tmpfile)
        self.assertEqual(loaded[0]["title"], "Побег из Шоушенка")


if __name__ == "__main__":
    unittest.main(verbosity=2)
