import tkinter as tk
import requests

API_URL = "https://openlibrary.org/search.json"


class BookRatingsApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Рейтинги книг")
    self.root.geometry("600x400")

    self.query_entry = tk.Entry(self.root, width=30)
    self.query_entry.pack(pady=10)

    self.search_btn = tk.Button(
        self.root, text="Найти", command=self.search_books
    )
    self.search_btn.pack()

    self.output_text = tk.Text(self.root, height=15, width=65)
    self.output_text.pack(pady=10)

  def search_books(self):
    query = self.query_entry.get().strip()
    if not query:
      return

    response = requests.get(API_URL, params={"q": query, "limit": 10})
    data = response.json()

    self.output_text.delete(1.0, tk.END)
    for doc in data.get("docs", []):
      title = doc.get("title", "Без названия")
      author = ", ".join(doc.get("author_name", ["Неизвестен"]))
      rating = doc.get("ratings_average")
      rating_str = f"{rating:.1f}" if rating else "нет оценок"
      self.output_text.insert(
          tk.END, f"{title} — {author} | Рейтинг: {rating_str}\n"
      )


if __name__ == "__main__":
  root = tk.Tk()
  app = BookRatingsApp(root)
  root.mainloop()