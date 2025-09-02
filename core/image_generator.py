import os
import re
import random
from typing import Optional, List

import requests
from io import BytesIO
from PIL import Image
from openai import OpenAI

from config.settings import OPENAI_API_KEY, PIXABAY_API_KEY, MAX_COVERS
from utils.image_registry import (
    is_used,
    mark_used,
    is_file_saved,
    mark_file_saved,
    has_file_hash,
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
Расширена генерация: поддержка нескольких базовых запросов от GPT.
"""


def generate_search_candidates(summary: str) -> List[str]:
    """Возвращает 5-10 коротких англ. запросов (тегов) на основе сводки.
    Пример ответа GPT: "trading floor, candlestick chart, stock exchange, financial district, bull and bear, gold bars, oil barrels, central bank, press conference".
    """
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.4,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты помощник по поиску реальных фото для финансовой темы. "
                        "Верни 6-10 коротких АНГЛИЙСКИХ фраз (1-3 слова каждая), через запятую. "
                        "Фокус: рынки/трейдинг/деньги/банки/сырьё/экономика: trading floor, candlestick chart, stock exchange, trader at desk, financial district skyline, bull and bear, gold bars, oil barrels, energy market, central bank building, press conference, newspaper finance section. "
                        "Игнорируй электронику и железо (computer, PSU, cable). Верни только список, без пояснений."
                    ),
                },
                {"role": "user", "content": summary},
            ],
        )
        raw = resp.choices[0].message.content or ""
        # Разделим по запятым/строкам
        parts = re.split(r"[,\n]+", raw)
        clean = []
        seen = set()
        for p in parts:
            q = sanitize_query(p)
            if not q:
                continue
            q = enrich_query(q)
            k = q.lower()
            if k in seen:
                continue
            seen.add(k)
            clean.append(q)
            if len(clean) >= 10:
                break
        # Если ничего не вышло — подстрахуемся базой
        if not clean:
            clean = ["trading floor", "stock market", "candlestick chart", "financial district", "stock exchange building"]
        return clean
    except Exception as exc:
        print(f"Ошибка генерации списка поисковых запросов: {exc}")
        return ["trading floor", "stock market", "candlestick chart", "banking"]


def _expand_query_variants(base: str) -> list:
    base = enrich_query(base)
    extras = [
        "trading floor",
        "trader at desk",
        "candlestick chart",
        "stock market",
        "stock exchange",
        "ticker",
        "financial markets",
        "financial district",
        "banking",
        "central bank",
        "press conference",
        "newspaper finance",
        "bull and bear",
        "gold bars",
        "oil barrels",
        "energy market",
        "forex trading",
        "cryptocurrency market",
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
    return uniq[:10]


def search_pixabay_image(query) -> str:
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
            # q зададим ниже по вариантам
            "image_type": "photo",
            "orientation": "all",
            "safesearch": "true",
            "per_page": 20,
            "order": "popular",
            "lang": "en",
        }
        base_list: List[str]
        if isinstance(query, (list, tuple)):
            base_list = list(query)
        else:
            base_list = [str(query)]

        # Сформируем общий пул вариантов на основе всех базовых запросов
        variants: List[str] = []
        for base in base_list:
            variants.extend(_expand_query_variants(base))
        # Добавим слегка зашумлённые варианты
        rand_suffix = ["global markets", "economy", "wall street", "business"]
        for b in base_list[:3]:
            for s in rand_suffix:
                v = enrich_query(f"{b} {s}")[:80]
                if v.lower() not in [x.lower() for x in variants]:
                    variants.append(v)

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
        candidates = generate_search_candidates(prompt)
        # Подстрахуемся от повторов: до 3 волн с дополнительным шумом
        last_error = None
        image_url = None
        for attempt in range(1, 4):
            try:
                image_url = search_pixabay_image(candidates)
                break
            except Exception as e:
                last_error = e
                # добавим шум к каждому кандидату
                noisy = [enrich_query(f"{c} {random.choice(['global', 'markets', 'finance', 'economy'])}")[:80] for c in candidates]
                candidates = list(dict.fromkeys(noisy))  # dedup, сохранить порядок
        if not image_url:
            raise last_error or RuntimeError("No image found")

        print("Загружаем изображение...")
        resp = requests.get(image_url, timeout=30)
        resp.raise_for_status()

        # Определяем уникальное имя
        os.makedirs("data/covers", exist_ok=True)
        # Извлечём id из URL (хэш/числа перед _<size> .jpg/.jpeg/.png)
        uniq_id = None
        match = re.search(r"/get/([^/_]+)_\d+\.(?:jpg|jpeg|png)$", image_url, re.IGNORECASE)
        if match:
            uniq_id = match.group(1)
        if not uniq_id:
            # Фолбэк: хэш URL, чтобы гарантировать уникальность
            import hashlib
            uniq_id = hashlib.sha1(image_url.encode("utf-8")).hexdigest()[:40]
        unique_name = f"data/covers/{uniq_id}.png"

        # Перекодируем в PNG, чтобы расширение совпадало с содержимым
        # Проверим хэш содержимого до сохранения, чтобы не повторять обложки
        import hashlib
        content_hash = hashlib.sha256(resp.content).hexdigest()
        if has_file_hash(content_hash):
            print("⚠️ Скачанное изображение ранее уже использовалось (по содержимому). Пробуем другой вариант...")
            # Вторая попытка: другой вариант запроса
            try:
                alt_query = enrich_query(search_query + " finance markets")[:80]
                image_url = search_pixabay_image(alt_query)
                resp = requests.get(image_url, timeout=30)
                resp.raise_for_status()
                content_hash = hashlib.sha256(resp.content).hexdigest()
                if has_file_hash(content_hash):
                    print("⚠️ Повтор и по альтернативе. Оставляем как есть, чтобы не зациклиться.")
                else:
                    # обновим uniq_id по второму URL
                    match = re.search(r"/get/([^/_]+)_\d+\.(?:jpg|jpeg|png)$", image_url, re.IGNORECASE)
                    if match:
                        uniq_id = match.group(1)
                    unique_name = f"data/covers/{uniq_id}.png"
            except Exception as _e:
                pass

        try:
            img = Image.open(BytesIO(resp.content)).convert("RGB")
            img.save(unique_name, format="PNG")
        except Exception:
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
        return unique_name
    except Exception as exc:
        print(f"Ошибка получения изображения: {exc}")
        return None
