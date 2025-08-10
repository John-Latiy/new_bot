import os
from typing import Optional

import requests
from openai import OpenAI

from config.settings import OPENAI_API_KEY, PEXELS_API_KEY
from utils.image_registry import is_used, mark_used


# Клиент OpenAI для генерации поисковых запросов
client = OpenAI(api_key=OPENAI_API_KEY)


def generate_search_query(summary: str) -> str:
    """Сгенерировать короткий англ. запрос (1-3 слова) под фото на Pexels."""
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты помощник для поиска изображений. На основе "
                        "финансовой сводки создай короткий англ. запрос "
                        "(1-3 слова) для РЕАЛЬНОГО фото (не AI). Темы: "
                        "finance, business, stock market, crypto, economy, "
                        "banking, money, investment, technology, industry. "
                        "Верни только запрос."
                    ),
                },
                {"role": "user", "content": summary},
            ],
        )
        query = (resp.choices[0].message.content or "").strip()
        print(f"Поисковый запрос для Pexels: {query}")
        return query or "finance business"
    except Exception as exc:
        print(f"Ошибка генерации поискового запроса: {exc}")
        return "finance business"


def search_pexels_image(query: str) -> str:
    """Ищет изображение на Pexels и возвращает прямой URL."""
    try:
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": PEXELS_API_KEY or ""}
        params = {
            "query": query,
            "per_page": 15,
            "orientation": "square",
            "size": "large",
        }

        resp = requests.get(
            url, headers=headers, params=params, timeout=20
        )
        resp.raise_for_status()
        data = resp.json()
        photos = data.get("photos") or []
        if photos:
            # выбирать первый неиспользованный ранее кадр
            for p in photos:
                image_id = str(p.get("id"))
                if image_id and is_used("pexels", image_id):
                    continue
                src = p.get("src") or {}
                image_url = (
                    src.get("large2x")
                    or src.get("large")
                    or src.get("medium")
                    or src.get("original")
                )
                if image_url:
                    print(f"Найдено изображение: {image_url}")
                    # отметим как использованное
                    mark_used("pexels", image_id or "", image_url, query)
                    return image_url

        print("Изображения не найдены, используем запасной вариант")
        return (
            "https://images.pexels.com/photos/210607/pexels-photo-210607.jpeg"
        )
    except Exception as exc:
        print(f"Ошибка поиска в Pexels: {exc}")
        return (
            "https://images.pexels.com/photos/210607/pexels-photo-210607.jpeg"
        )


def generate_image(
    prompt: str, filename: str = "data/final_cover.png"
) -> Optional[str]:
    """Находит изображение на Pexels и сохраняет локально."""
    try:
        print("Поиск изображения на Pexels по теме...")
        search_query = generate_search_query(prompt)
        image_url = search_pexels_image(search_query)

        print("Загружаем изображение...")
        resp = requests.get(image_url, timeout=30)
        resp.raise_for_status()

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as f:
            f.write(resp.content)

        print(f"Изображение сохранено: {filename}")
        return filename
    except Exception as exc:
        print(f"Ошибка получения изображения: {exc}")
        return None
