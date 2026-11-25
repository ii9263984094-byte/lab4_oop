import tkinter as tk
from tkinter import messagebox
import requests

API_URL = "https://openlibrary.org/search.json"


class BookRatingsApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Рейтинги книг")
    self.root.geometry("680x440")
    self.root.minsize(500, 320)

    self.query_entry = tk.Entry(self.root, width=35, font=("Arial", 11))
    self.query_entry.pack(pady=(12, 6))
    self.query_entry.bind("<Return>", lambda event: self.search_books())

    self.search_btn = tk.Button(
        self.root, text="Найти", command=self.search_books, width=14
    )
    self.search_btn.pack(pady=(0, 10))

    self.output_text = tk.Text(
        self.root,
        height=16,
        width=75,
        font=("Arial", 10),
        wrap=tk.WORD,
        padx=8,
        pady=8,
    )
    self.output_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

  def fetch_books(self, query):
    """Запрашивает список книг у Open Library API с обработкой ошибок."""
    try:
      response = requests.get(
          API_URL, params={"q": query, "limit": 15}, timeout=10
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
    """Проверяет ввод пользователя и выводит результаты поиска."""
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

    docs = data.get("docs", [])
    self.output_text.delete(1.0, tk.END)

    if not docs:
      messagebox.showinfo(
          "Ничего не найдено",
          f"По запросу «{query}» книги не найдены. Попробуйте другой запрос.",
      )
      return

    for idx, doc in enumerate(docs, start=1):
      title = doc.get("title", "Без названия")
      authors = ", ".join(doc.get("author_name", ["Неизвестен"]))
      rating = doc.get("ratings_average")
      rating_str = f"{rating:.2f} / 5.00" if rating is not None else "нет оценок"
      self.output_text.insert(
          tk.END, f"{idx}. {title} — {authors} | Рейтинг: {rating_str}\n"
      )


if __name__ == "__main__":
  root = tk.Tk()
  app = BookRatingsApp(root)
  root.mainloop()