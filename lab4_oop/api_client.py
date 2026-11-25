import requests


class BookApiClient:
  """Клиент для поиска книг и получения их рейтингов через Open Library API."""

  BASE_URL = "https://openlibrary.org/search.json"

  def search_books(self, query, limit=20):
    response = requests.get(
        self.BASE_URL,
        params={"q": query, "limit": limit},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()

    books = []
    for doc in payload.get("docs", []):
      books.append({
          "key": doc.get("key", ""),
          "title": doc.get("title", "Без названия"),
          "authors": ", ".join(doc.get("author_name", ["Неизвестен"])),
          "year": doc.get("first_publish_year", "—"),
          "rating": doc.get("ratings_average"),
          "ratings_count": doc.get("ratings_count", 0),
      })
    return books