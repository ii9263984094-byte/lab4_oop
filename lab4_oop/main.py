import json
import os
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import requests

API_URL = "https://openlibrary.org/search.json"
SETTINGS_FILE = "settings.json"


class BookRatingsApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Рейтинги книг")
    self.root.geometry("860x600")
    self.root.minsize(700, 440)

    self.settings = self.load_settings()
    self.books = []
    self.selected_book = None

    self.create_widgets()
    self.update_favorites_list()
    self.apply_theme()

  def load_settings(self):
    """Загружает настройки темы и список избранного из JSON-файла."""
    default = {"theme": "light", "favorites": []}
    if not os.path.exists(SETTINGS_FILE):
      return default
    try:
      with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
      return {
          "theme": data.get("theme", "light"),
          "favorites": data.get("favorites", []),
      }
    except (json.JSONDecodeError, OSError):
      return default

  def save_settings(self):
    """Сохраняет настройки темы и избранное в JSON-файл."""
    try:
      with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(self.settings, f, ensure_ascii=False, indent=4)
    except OSError as err:
      messagebox.showerror(
          "Ошибка сохранения", f"Не удалось записать настройки: {err}"
      )

  def create_widgets(self):
    """Создаёт панель поиска, списки книг/избранного и карточку книги."""
    top_frame = tk.Frame(self.root, padx=10, pady=10)
    top_frame.pack(fill=tk.X)

    tk.Label(top_frame, text="Запрос:", font=("Arial", 10)).pack(
        side=tk.LEFT, padx=(0, 5)
    )
    self.query_entry = tk.Entry(top_frame, width=28, font=("Arial", 11))
    self.query_entry.pack(side=tk.LEFT, padx=5)
    self.query_entry.bind("<Return>", lambda event: self.search_books())

    self.sort_combo = ttk.Combobox(
        top_frame,
        values=["По релевантности", "По рейтингу (убывание)"],
        state="readonly",
        width=22,
    )
    self.sort_combo.current(0)
    self.sort_combo.pack(side=tk.LEFT, padx=5)
    self.sort_combo.bind("<<ComboboxSelected>>", lambda event: self.sort_books())

    tk.Button(
        top_frame, text="Найти", command=self.search_books, width=10
    ).pack(side=tk.LEFT, padx=5)
    tk.Button(top_frame, text="Сменить тему", command=self.toggle_theme).pack(
        side=tk.RIGHT, padx=5
    )

    main_frame = tk.Frame(self.root, padx=10, pady=5)
    main_frame.pack(fill=tk.BOTH, expand=True)

    left_frame = tk.Frame(main_frame, width=320)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

    tk.Label(left_frame, text="Найденные книги:", font=("Arial", 10, "bold")).pack(
        anchor=tk.W
    )
    self.books_listbox = tk.Listbox(left_frame, width=44, height=14)
    self.books_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
    self.books_listbox.bind("<<ListboxSelect>>", self.on_book_select)

    tk.Label(left_frame, text="Избранное:", font=("Arial", 10, "bold")).pack(
        anchor=tk.W, pady=(10, 0)
    )
    self.fav_listbox = tk.Listbox(left_frame, width=44, height=8)
    self.fav_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
    self.fav_listbox.bind("<<ListboxSelect>>", self.on_favorite_select)

    right_frame = tk.Frame(main_frame)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    header_frame = tk.Frame(right_frame)
    header_frame.pack(fill=tk.X)

    self.book_title_label = tk.Label(
        header_frame,
        text="Выберите книгу",
        font=("Arial", 14, "bold"),
        wraplength=420,
        justify=tk.LEFT,
    )
    self.book_title_label.pack(side=tk.LEFT, anchor=tk.W)

    self.fav_btn = tk.Button(
        header_frame,
        text="В избранное",
        command=self.add_to_favorites,
        state=tk.DISABLED,
    )
    self.fav_btn.pack(side=tk.RIGHT)

    self.details_text = scrolledtext.ScrolledText(
        right_frame, wrap=tk.WORD, font=("Arial", 11), state=tk.DISABLED
    )
    self.details_text.pack(fill=tk.BOTH, expand=True, pady=10)

  def fetch_books(self, query):
    """Запрашивает список книг у Open Library API с обработкой ошибок."""
    try:
      response = requests.get(
          API_URL, params={"q": query, "limit": 20}, timeout=10
      )
      response.raise_for_status()
      return response.json()
    except requests.exceptions.ConnectionError:
      messagebox.showerror(
          "Ошибка сети",
          "Нет подключения к интернету или сервер Open Library недоступен.",
      )
    except requests.exceptions.Timeout:
      messagebox.showerror(
          "Таймаут", "Сервер слишком долго не отвечает. Попробуйте позже."
      )
    except requests.exceptions.RequestException as err:
      messagebox.showerror(
          "Ошибка запроса", f"Не удалось получить данные с сервера:\n{err}"
      )
    except ValueError:
      messagebox.showerror(
          "Ошибка данных", "Сервер вернул некорректный ответ (не JSON)."
      )
    return None

  def search_books(self):
    """Выполняет поиск книг по запросу пользователя и обновляет список."""
    query = self.query_entry.get().strip()
    if not query:
      messagebox.showwarning(
          "Пустой запрос", "Введите название книги или имя автора."
      )
      self.query_entry.focus_set()
      return

    data = self.fetch_books(query)
    if not data:
      return

    raw_docs = data.get("docs", [])
    self.books = []
    for doc in raw_docs:
      self.books.append({
          "key": doc.get("key", ""),
          "title": doc.get("title", "Без названия"),
          "authors": ", ".join(doc.get("author_name", ["Неизвестен"])),
          "year": doc.get("first_publish_year", "—"),
          "rating": doc.get("ratings_average"),
          "ratings_count": doc.get("ratings_count", 0),
      })

    self.books_listbox.delete(0, tk.END)
    if not self.books:
      messagebox.showinfo(
          "Результаты",
          f"По запросу «{query}» книги не найдены. Попробуйте другой запрос.",
      )
      return

    self.sort_books()

  def sort_books(self):
    """Сортирует найденные книги и перерисовывает Listbox."""
    if not self.books:
      return

    if self.sort_combo.get() == "По рейтингу (убывание)":
      self.books.sort(
          key=lambda b: b["rating"] if b["rating"] is not None else -1.0,
          reverse=True,
      )

    self.books_listbox.delete(0, tk.END)
    for book in self.books:
      rating_text = (
          f"{book['rating']:.2f}★" if book["rating"] is not None else "б/о"
      )
      self.books_listbox.insert(
          tk.END, f"[{rating_text}] {book['title']} ({book['year']})"
      )

  def on_book_select(self, event):
    """Обрабатывает выбор книги из списка результатов поиска."""
    selection = self.books_listbox.curselection()
    if not selection:
      return
    self.display_book(self.books[selection[0]])

  def on_favorite_select(self, event):
    """Открывает карточку книги по клику в списке избранного."""
    selection = self.fav_listbox.curselection()
    if not selection:
      return
    fav_book = self.settings["favorites"][selection[0]]
    self.display_book(fav_book)

  def display_book(self, book):
    """Отображает подробную информацию о книге и активирует кнопку избранного."""
    self.selected_book = book
    self.book_title_label.config(text=book["title"])
    self.fav_btn.config(state=tk.NORMAL)

    rating_val = book.get("rating")
    rating_count = book.get("ratings_count", 0)
    rating_str = (
        f"{rating_val:.2f} / 5.00 ({rating_count} оценок)"
        if rating_val is not None
        else "Оценок пока нет"
    )

    info = (
        f"Автор(ы): {book.get('authors', 'Неизвестен')}\n"
        f"Первый год издания: {book.get('year', '—')}\n"
        f"Рейтинг: {rating_str}\n"
        f"{'-' * 45}\n"
        f"Ключ Open Library: {book.get('key', '—')}"
    )
    self.details_text.config(state=tk.NORMAL)
    self.details_text.delete(1.0, tk.END)
    self.details_text.insert(tk.END, info)
    self.details_text.config(state=tk.DISABLED)

  def add_to_favorites(self):
    """Добавляет выбранную книгу в избранное без дубликатов и сохраняет в JSON."""
    if not self.selected_book:
      return

    for item in self.settings["favorites"]:
      if (
          item.get("key") == self.selected_book.get("key")
          and item.get("title") == self.selected_book.get("title")
          and item.get("authors") == self.selected_book.get("authors")
      ):
        messagebox.showinfo("Избранное", "Эта книга уже есть в избранном.")
        return

    self.settings["favorites"].append(self.selected_book)
    self.save_settings()
    self.update_favorites_list()
    messagebox.showinfo("Успех", "Книга добавлена в избранное.")

  def update_favorites_list(self):
    """Обновляет виджет списка избранных книг."""
    self.fav_listbox.delete(0, tk.END)
    for item in self.settings["favorites"]:
      self.fav_listbox.insert(tk.END, f"{item['title']} — {item['authors']}")

  def toggle_theme(self):
    """Переключает светлую и тёмную тему и сохраняет выбор."""
    self.settings["theme"] = (
        "dark" if self.settings["theme"] == "light" else "light"
    )
    self.save_settings()
    self.apply_theme()

  def apply_theme(self):
    """Применяет выбранную цветовую схему ко всему окну и виджетам."""
    is_dark = self.settings["theme"] == "dark"
    bg = "#2b2b2b" if is_dark else "#f0f0f0"
    fg = "#ffffff" if is_dark else "#000000"
    field_bg = "#3c3f41" if is_dark else "#ffffff"
    btn_bg = "#4a4d50" if is_dark else "#e1e1e1"
    scroll_bg = "#3c3f41" if is_dark else "#f0f0f0"

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "TCombobox",
        fieldbackground=field_bg,
        background=btn_bg,
        foreground=fg,
        arrowcolor=fg,
    )

    self.root.configure(bg=bg)
    for child in self.root.winfo_children():
      self._apply_theme_recursive(child, bg, fg, field_bg, btn_bg, scroll_bg)

  def _apply_theme_recursive(self, widget, bg, fg, field_bg, btn_bg, scroll_bg):
    try:
      if isinstance(widget, (tk.Frame, tk.Label)):
        widget.configure(bg=bg, fg=fg)
      elif isinstance(widget, tk.Button):
        widget.configure(
            bg=btn_bg,
            fg=fg,
            activebackground=(
                "#5a5e63" if self.settings["theme"] == "dark" else "#d0d0d0"
            ),
            activeforeground=fg,
        )
      elif isinstance(widget, scrolledtext.ScrolledText):
        widget.configure(bg=field_bg, fg=fg, insertbackground=fg)
        if hasattr(widget, "vbar"):
          widget.vbar.configure(
              bg=scroll_bg, troughcolor=bg, activebackground=btn_bg
          )
      elif isinstance(widget, tk.Listbox):
        widget.configure(
            bg=field_bg,
            fg=fg,
            selectbackground=(
                "#4b6eaf" if self.settings["theme"] == "dark" else "#0078d7"
            ),
            selectforeground="#ffffff",
        )
      elif isinstance(widget, tk.Entry):
        widget.configure(bg=field_bg, fg=fg, insertbackground=fg)
    except tk.TclError:
      pass

    for child in widget.winfo_children():
      self._apply_theme_recursive(child, bg, fg, field_bg, btn_bg, scroll_bg)


if __name__ == "__main__":
  root = tk.Tk()
  app = BookRatingsApp(root)
  root.mainloop()