import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Обязательно загружаем .env в этом файле
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Переменная окружения OPENAI_API_KEY не найдена!")

client = OpenAI(api_key=api_key)

def generate_summary(posts: list[str]) -> str:
    """Генерирует сводку. Встроены повторы при таймаутах и безопасный фолбэк."""
    if not posts:
        return "⚠️ Ошибка: нет текстов для анализа."

    combined_text = "\n".join(posts)

    system_prompt = (
        """
Ты финансовый аналитик и контент-мейкер.
На основе списка новостей сформируй связную, лаконичную, но живую сводку.
Пиши так, чтобы текст было интересно читать даже тем, кто не эксперт.
Используй деловой, но дружелюбный тон — добавляй немного эмоций, метафор и простых примеров.
Разбивай текст на короткие абзацы для удобства чтения.
Вставляй уместные эмодзи, но не перегружай ими пост.
Добавляй риторические вопросы или небольшие «крючки», которые вовлекают читателя.
Пост не должен превышать 2200 символов.
Не используй хештеги из исходных новостей и не добавляй ссылки.
В конце придумай 3–6 хештегов, отражающих суть поста.
Обязательно придумывай креативный заголовок, ставь его в кавычки.
Текст поста начинай с новой строки под заголовком.
"""
    )

    # Попробуем несколько раз на случай сетевых таймаутов
    attempts = 3
    backoff = 3.0
    last_err: Exception | None = None
    for i in range(1, attempts + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": combined_text},
                ],
                temperature=0.7,
                timeout=30,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Считаем это временной ошибкой и повторим
            last_err = e
            # Для последних попыток не ждём
            if i < attempts:
                time.sleep(backoff)
                backoff *= 1.6

    # Фолбэк: короткий дайджест по первым пунктам, чтобы не срывать выпуск
    try:
        bullets = []
        for p in posts[:4]:
            p = (p or "").strip().replace("\n", " ")
            if len(p) > 260:
                p = p[:257] + "…"
            if p:
                bullets.append(f"• {p}")
        body = "\n".join(bullets)
        fallback = (
            '"Краткий утренний дайджест"\n'
            f"{body}\n\n#Экономика #Финансы #Рынки"
        )
        return fallback
    except Exception:
        # В крайнем случае вернём исходную ошибку
        return f"⚠️ Ошибка генерации сводки: {last_err}"
