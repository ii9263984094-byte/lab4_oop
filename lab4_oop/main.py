import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import requests

API_URL = "https://openlibrary.org/search.json"


class BookRatingsApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Рейтинги книг")
    self.root.geometry("820x560")
    self.root.minsize(680, 420)

    self.books = []
    self.selected_book = None

    self.create_widgets()

  def create_widgets(self):
    """Создаёт верхнюю панель поиска и двухколоночную область результатов."""
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

    main_frame = tk.Frame(self.root, padx=10, pady=5)
    main_frame.pack(fill=tk.BOTH, expand=True)

    left_frame = tk.Frame(main_frame, width=320)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

    tk.Label(left_frame, text="Найденные книги:", font=("Arial", 10, "bold")).pack(
        anchor=tk.W
    )
    self.books_listbox = tk.Listbox(left_frame, width=44, height=22)
    self.books_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
    self.books_listbox.bind("<<ListboxSelect>>", self.on_book_select)

    right_frame = tk.Frame(main_frame)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    self.book_title_label = tk.Label(
        right_frame,
        text="Выберите книгу из списка",
        font=("Arial", 14, "bold"),
        wraplength=460,
        justify=tk.LEFT,
    )
    self.book_title_label.pack(anchor=tk.W)

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
    """Обрабатывает клик по строке списка книг и выводит карточку."""
    selection = self.books_listbox.curselection()
    if not selection:
      return
    book = self.books[selection[0]]
    self.selected_book = book
    self.display_book(book)

  def display_book(self, book):
    """Отображает подробную информацию о выбранной книге в правой панели."""
    self.book_title_label.config(text=book["title"])
    rating_str = (
        f"{book['rating']:.2f} / 5.00 ({book['ratings_count']} оценок)"
        if book["rating"] is not None
        else "Оценок пока нет"
    )
    info = (
        f"Автор(ы): {book['authors']}\n"
        f"Первый год издания: {book['year']}\n"
        f"Рейтинг: {rating_str}\n"
        f"{'-' * 45}\n"
        f"Идентификатор записи: {book['key']}"
    )
    self.details_text.config(state=tk.NORMAL)
    self.details_text.delete(1.0, tk.END)
    self.details_text.insert(tk.END, info)
    self.details_text.config(state=tk.DISABLED)


if __name__ == "__main__":
  root = tk.Tk()
  app = BookRatingsApp(root)
  root.mainloop()