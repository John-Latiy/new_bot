import os
from typing import Optional
import re

import requests
from openai import OpenAI

from config.settings import (
    OPENAI_API_KEY,
    PEXELS_API_KEY,
    PIXABAY_API_KEY,
)
from utils.image_registry import is_used, mark_used


# Клиент OpenAI для генерации поисковых запросов
client = OpenAI(api_key=OPENAI_API_KEY)


def sanitize_query(q: str) -> str:
    """Привести запрос к опрятному виду: убрать маркеры списков,
    лишние пробелы.
    """
    q = (q or "").strip()
    q = re.sub(r"^[^A-Za-z0-9]+", "", q)  # убрать ведущие дефисы/маркеры
    q = re.sub(r"\s+", " ", q)
    return q


# Тематические фильтры
FINANCE_WHITELIST = [
    "finance",
    "financial",
    "stock",
    "stocks",
    "market",
    "stock market",
    "trading",
    "trader",
    "chart",
    "charts",
    "candlestick",
    "ticker",
    "forex",
    "exchange",
    "economy",
    "bank",
    "money",
    "investment",
]

BLACKLIST = [
    "power supply",
    "psu",
    "computer",
    "motherboard",
    "gpu",
    "cpu",
    "cable",
    "plug",
    "socket",
    "server",
    "electronics",
]


def is_finance_related(text: str) -> bool:
    t = (text or "").lower()
    return any(w in t for w in FINANCE_WHITELIST)


def has_blacklisted(text: str) -> bool:
    t = (text or "").lower()
    return any(b in t for b in BLACKLIST)


def enrich_query(q: str) -> str:
    q = sanitize_query(q)
    # Убираем явные "железные" термины
    for b in BLACKLIST:
        q = re.sub(rf"\b{re.escape(b)}\b", "", q, flags=re.IGNORECASE)
    q = q.strip()
    # Добавим якорь тематики, если не хватает
    if not is_finance_related(q):
        q = (q + " stock market").strip()
    return q


def generate_search_query(summary: str) -> str:
    """Сгенерировать короткий англ. запрос (1-3 слова) под фото на тему
    финансов/рынков; с последующим обогащением и чисткой.
    """
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты помощник по поиску фотографий ДЛЯ ФИНАНСОВОЙ "
                        "ТЕМАТИКИ. На основе сводки верни только короткий "
                        "англ. запрос (1-3 слова) для реального фото (не AI). "
                        "Сфокусируйся на рынках/трейдинге/деньгах: "
                        "stock market, trading floor, candlestick chart, "
                        "ticker, bank, money. "
                        "Игнорируй электронику/железо (computer, PSU, "
                        "cable и т.п.). "
                        "Верни только запрос."
                    ),
                },
                {"role": "user", "content": summary},
            ],
        )
        query = enrich_query(resp.choices[0].message.content or "")
        print("Поисковый запрос: " + query)
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
            "query": enrich_query(query),
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
                alt = p.get("alt") or ""
                # Фильтрация по описанию
                if (
                    has_blacklisted(alt)
                    or not is_finance_related(alt + " " + query)
                ):
                    continue
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


def search_pixabay_image(query: str) -> str:
    """Ищет изображение на Pixabay и возвращает прямой URL."""
    try:
        url = "https://pixabay.com/api/"
        params = {
            "key": PIXABAY_API_KEY or "",
            "q": enrich_query(query),
            "image_type": "photo",
            "orientation": "horizontal",
            "safesearch": "true",
            "per_page": 20,
            "order": "popular",
            "category": "business",
            "lang": "en",
        }
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits") or []
        if hits:
            for h in hits:
                image_id = str(h.get("id"))
                if image_id and is_used("pixabay", image_id):
                    continue
                tags = h.get("tags") or ""
                # Фильтрация по тегам
                if (
                    has_blacklisted(tags)
                    or not is_finance_related(tags + " " + query)
                ):
                    continue
                image_url = (
                    h.get("largeImageURL")
                    or h.get("webformatURL")
                    or h.get("previewURL")
                )
                if image_url:
                    print(f"Найдено изображение (Pixabay): {image_url}")
                    mark_used("pixabay", image_id or "", image_url, query)
                    return image_url
        print("Pixabay: изображения не найдены, используем запасной вариант")
        return (
            "https://cdn.pixabay.com/photo/2016/11/18/15/49/"
            "chart-1839518_1280.jpg"
        )
    except Exception as exc:
        print(f"Ошибка поиска в Pixabay: {exc}")
        return (
            "https://cdn.pixabay.com/photo/2016/11/18/15/49/"
            "chart-1839518_1280.jpg"
        )


def generate_image(
    prompt: str, filename: str = "data/final_cover.png"
) -> Optional[str]:
    """Находит изображение (Pixabay → Pexels фолбэк) и сохраняет локально."""
    try:
        print("Поиск изображения (Pixabay → Pexels)...")
        search_query = generate_search_query(prompt)
        image_url = None
        # Сначала пробуем Pixabay (есть валидный ключ)
        if PIXABAY_API_KEY:
            image_url = search_pixabay_image(search_query)
        # Если не удалось или ключа нет — пробуем Pexels
        if not image_url and PEXELS_API_KEY:
            image_url = search_pexels_image(search_query)
        # Если всё пусто — финальный фолбэк
        if not image_url:
            image_url = (
                "https://cdn.pixabay.com/photo/2016/11/18/15/49/"
                "chart-1839518_1280.jpg"
            )

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
