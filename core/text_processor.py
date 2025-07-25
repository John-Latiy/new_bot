import os
from openai import OpenAI
from dotenv import load_dotenv

# Обязательно загружаем .env в этом файле
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Переменная окружения OPENAI_API_KEY не найдена!")

client = OpenAI(api_key=api_key)

def generate_summary(posts: list[str]) -> str:
    if not posts:
        return "⚠️ Ошибка: нет текстов для анализа."

    combined_text = "\n".join(posts)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                   "role": "system",
                "content": (
                    "Ты финансовый аналитик. На основе списка новостей сформируй лаконичную и связную сводку. "
                    "Пиши в деловом тоне, избегай повторов, не используй 'Вывод:'. "
                    "При оформлении поста используй эмодзи, но в меру, не перегружая пост."
                    "пост не должен привышать 2200 символов. не используй хештеги из полученных новостей, не добавляй сылки на сторонние ресурсы."
                    "в конце добавляй хештеги которые соответствуют посту который ты сгенерировал."
                    )
                },
                {"role": "user", "content": combined_text}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Ошибка генерации сводки: {e}"
