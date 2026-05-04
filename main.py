"""
Movie Library — главный модуль GUI-приложения.
Запускает окно tkinter с формой добавления, таблицей и фильтрацией фильмов.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from storage import load_movies, save_movies
from validator import validate_movie


class MovieLibraryApp:
    """Графическое приложение «Личная кинотека»."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("🎬 Movie Library — Личная кинотека")
        self.root.geometry("950x620")
        self.root.resizable(True, True)

        self.movies: list[dict] = load_movies()
        self._build_ui()
        self._refresh_table(self.movies)

    # ------------------------------------------------------------------ #
    #  Построение интерфейса                                               #
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        self._build_input_frame()
        self._build_filter_frame()
        self._build_table()
        self._build_bottom_bar()

    def _build_input_frame(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Добавить фильм", padding=10)
        frame.pack(fill="x", padx=12, pady=(8, 4))

        labels = ["Название:", "Жанр:", "Год выпуска:", "Рейтинг (0–10):"]
        widths = [28, 20, 10, 10]
        self.title_var  = tk.StringVar()
        self.genre_var  = tk.StringVar()
        self.year_var   = tk.StringVar()
        self.rating_var = tk.StringVar()
        vars_ = [self.title_var, self.genre_var, self.year_var, self.rating_var]

        for col, (lbl, var, w) in enumerate(zip(labels, vars_, widths)):
            ttk.Label(frame, text=lbl).grid(row=0, column=col * 2,     sticky="w", padx=(8, 2))
            ttk.Entry(frame, textvariable=var, width=w).grid(row=0, column=col * 2 + 1, padx=(0, 6))

        ttk.Button(frame, text="➕ Добавить фильм", command=self._add_movie).grid(
            row=0, column=8, padx=(12, 4)
        )

    def _build_filter_frame(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Фильтрация", padding=10)
        frame.pack(fill="x", padx=12, pady=4)

        ttk.Label(frame, text="Жанр:").grid(row=0, column=0, sticky="w", padx=(8, 2))
        self.filter_genre_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.filter_genre_var, width=20).grid(row=0, column=1, padx=(0, 10))

        ttk.Label(frame, text="Год:").grid(row=0, column=2, sticky="w", padx=(8, 2))
        self.filter_year_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.filter_year_var, width=10).grid(row=0, column=3, padx=(0, 10))

        ttk.Button(frame, text="🔍 Применить", command=self._apply_filter).grid(row=0, column=4, padx=4)
        ttk.Button(frame, text="↺ Сбросить",   command=self._reset_filter).grid(row=0, column=5, padx=4)

    def _build_table(self) -> None:
        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=12, pady=4)

        columns = ("title", "genre", "year", "rating")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")

        headings = {"title": "Название", "genre": "Жанр", "year": "Год", "rating": "Рейтинг"}
        col_widths = {"title": 310, "genre": 180, "year": 80, "rating": 90}

        for col in columns:
            self.tree.heading(col, text=headings[col],
                              command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=col_widths[col], anchor="center")

        self.tree.column("title", anchor="w")

        vsb = ttk.Scrollbar(frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _build_bottom_bar(self) -> None:
        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=12, pady=(4, 8))
        ttk.Button(frame, text="🗑 Удалить выбранный", command=self._delete_movie).pack(side="left")
        self.status_var = tk.StringVar(value="Готово.")
        ttk.Label(frame, textvariable=self.status_var, foreground="gray").pack(side="right")

    # ------------------------------------------------------------------ #
    #  Логика                                                              #
    # ------------------------------------------------------------------ #

    def _add_movie(self) -> None:
        title  = self.title_var.get().strip()
        genre  = self.genre_var.get().strip()
        year_s = self.year_var.get().strip()
        rate_s = self.rating_var.get().strip()

        ok, result = validate_movie(title, genre, year_s, rate_s)
        if not ok:
            messagebox.showerror("Ошибка ввода", result)
            return

        year, rating = result
        movie = {"title": title, "genre": genre, "year": year, "rating": rating}
        self.movies.append(movie)
        save_movies(self.movies)
        self._refresh_table(self.movies)

        for var in (self.title_var, self.genre_var, self.year_var, self.rating_var):
            var.set("")

        self._set_status(f"Добавлен: «{title}»")

    def _apply_filter(self) -> None:
        genre_f = self.filter_genre_var.get().strip().lower()
        year_f  = self.filter_year_var.get().strip()

        result = list(self.movies)

        if genre_f:
            result = [m for m in result if genre_f in m["genre"].lower()]

        if year_f:
            if not year_f.lstrip("-").isdigit():
                messagebox.showerror("Ошибка фильтра", "Год для фильтра должен быть целым числом.")
                return
            result = [m for m in result if m["year"] == int(year_f)]

        self._refresh_table(result)
        self._set_status(f"Найдено: {len(result)} фильм(ов)")

    def _reset_filter(self) -> None:
        self.filter_genre_var.set("")
        self.filter_year_var.set("")
        self._refresh_table(self.movies)
        self._set_status(f"Фильтр сброшен. Всего: {len(self.movies)}")

    def _delete_movie(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Удаление", "Выберите строку в таблице для удаления.")
            return

        values = self.tree.item(selected[0])["values"]
        title, genre, year, rating = values[0], values[1], int(values[2]), float(values[3])

        self.movies = [
            m for m in self.movies
            if not (m["title"] == title and m["genre"] == genre
                    and m["year"] == year and m["rating"] == rating)
        ]
        save_movies(self.movies)
        self._refresh_table(self.movies)
        self._set_status(f"Удалён: «{title}»")

    def _refresh_table(self, movies: list[dict]) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for m in movies:
            self.tree.insert("", "end", values=(m["title"], m["genre"], m["year"], m["rating"]))

    def _sort_by(self, col: str) -> None:
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children("")]
        try:
            data.sort(key=lambda x: float(x[0]))
        except ValueError:
            data.sort(key=lambda x: x[0].lower())
        for index, (_, child) in enumerate(data):
            self.tree.move(child, "", index)

    def _set_status(self, msg: str) -> None:
        self.status_var.set(msg)


def main() -> None:
    root = tk.Tk()
    MovieLibraryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
