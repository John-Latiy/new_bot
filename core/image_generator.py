import os
import re
import random
from typing import Optional

import requests
from openai import OpenAI

from config.settings import OPENAI_API_KEY, PIXABAY_API_KEY, MAX_COVERS
from utils.image_registry import (
    is_used,
    mark_used,
    is_file_saved,
    mark_file_saved,
)


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


"""
Оставлена только интеграция с Pixabay. Путь Pexels удалён.
"""


def _expand_query_variants(base: str) -> list:
    base = enrich_query(base)
    extras = [
        "trading floor",
        "candlestick chart",
        "stock market",
        "financial markets",
        "banking",
        "forex trading",
    ]
    variants = [base]
    for e in extras:
        if e.lower() not in base.lower():
            variants.append(f"{base} {e}"[:80])
    # Deduplicate preserving order
    seen = set()
    uniq = []
    for v in variants:
        k = v.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(v)
    return uniq[:6]


def search_pixabay_image(query: str) -> str:
    """Ищет изображение на Pixabay и возвращает прямой URL.
    Улучшено: собираем все новые подходящие изображения и случайно
    выбираем одно, чтобы снизить повторяемость.
    """
    try:
        if not (PIXABAY_API_KEY and PIXABAY_API_KEY.strip()):
            raise RuntimeError("PIXABAY_API_KEY is missing. Set it in .env")
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
        variants = _expand_query_variants(query)
        total_used_skipped = 0
        for idx, variant in enumerate(variants, 1):
            pv = {**params, "q": variant}
            try:
                resp = requests.get(url, params=pv, timeout=20)
                resp.raise_for_status()
            except Exception as e:
                print(f"⚠️ Ошибка запроса Pixabay (вариант {idx}/{len(variants)}: '{variant}'): {e}")
                continue
            data = resp.json()
            hits = data.get("hits") or []
            candidates = []
            used_skipped = 0
            for h in hits:
                image_id = str(h.get("id"))
                if image_id and is_used("pixabay", image_id):
                    used_skipped += 1
                    continue
                tags = h.get("tags") or ""
                if has_blacklisted(tags) or not is_finance_related(tags + " " + variant):
                    continue
                image_url = (
                    h.get("largeImageURL")
                    or h.get("webformatURL")
                    or h.get("previewURL")
                )
                if image_url:
                    candidates.append((image_id, image_url))
            total_used_skipped += used_skipped
            if candidates:
                random.shuffle(candidates)
                image_id, image_url = candidates[0]
                print(
                    f"Найдено изображение (Pixabay): {image_url} | вариант запроса {idx}/{len(variants)} '{variant}', кандидатов: {len(candidates)}, пропущено ранее использованных: {used_skipped}, суммарно пропущено: {total_used_skipped}"
                )
                mark_used("pixabay", image_id or "", image_url, variant)
                return image_url
            else:
                print(f"Вариант '{variant}' не дал новых изображений (used skipped={used_skipped}).")
        print(
            f"Pixabay: не найдено новых изображений. Всего пропущено уже использованных: {total_used_skipped}."
        )
        raise RuntimeError("No suitable Pixabay images found for query (all variants exhausted)")
    except Exception as exc:
        print(f"Ошибка поиска в Pixabay: {exc}")
        raise


def generate_image(
    prompt: str, filename: str = "data/final_cover.png"
) -> Optional[str]:
    """Находит изображение в Pixabay и сохраняет локально.
    Теперь сохраняем под уникальным именем вида data/covers/<id>.png, а
    также обновляем симлинк/копию final_cover.png для совместимости.
    """
    try:
        print("Поиск изображения (Pixabay)...")
        search_query = generate_search_query(prompt)
        image_url = search_pixabay_image(search_query)

        print("Загружаем изображение...")
        resp = requests.get(image_url, timeout=30)
        resp.raise_for_status()

        # Определяем уникальное имя
        os.makedirs("data/covers", exist_ok=True)
        # Извлечём id из URL (цифры перед _1280 / .jpg) как image_id
        uniq_id = None
        match = re.search(r"/(g?[0-9a-f]{10,}|\d+)_\d+\.jpg", image_url)
        if match:
            uniq_id = match.group(1)
        if not uniq_id:
            uniq_id = re.sub(r"\W+", "", search_query.lower())[:20]
        unique_name = f"data/covers/{uniq_id}.png"

        with open(unique_name, "wb") as f:
            f.write(resp.content)
        mark_file_saved(unique_name)

        # Синхронизируем совместимый путь final_cover.png
        try:
            # Копируем (не ссылка) чтобы внешние загрузчики работали одинаково
            import shutil
            shutil.copyfile(unique_name, filename)
        except Exception as _e:
            pass

        # Ротация: ограничиваем число файлов в data/covers
        try:
            covers = sorted(
                [
                    os.path.join("data/covers", f)
                    for f in os.listdir("data/covers")
                    if f.lower().endswith(".png")
                ],
                key=lambda p: os.path.getmtime(p),
            )
            if len(covers) > MAX_COVERS:
                to_delete = covers[: len(covers) - MAX_COVERS]
                for old in to_delete:
                    try:
                        os.remove(old)
                        print(f"🧹 Удалён старый cover: {old}")
                    except Exception:
                        pass
        except Exception as rot_e:
            print(f"⚠️ Ошибка ротации обложек: {rot_e}")

        print(f"Изображение сохранено: {unique_name} (и обновлён {filename})")
        return filename
    except Exception as exc:
        print(f"Ошибка получения изображения: {exc}")
        return None
