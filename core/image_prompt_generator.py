# core/image_prompt_generator.py

from openai import OpenAI
from config.settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Ты помощник для поиска изображений. На основе финансовой сводки создай текст, который поможет найти подходящее изображение.

Сосредоточься на основных темах новостей: финансы, экономика, криптовалюты, фондовый рынок, банки, инвестиции, технологии, промышленность.

Создай короткое описание (1-2 предложения) основной темы новостей для последующего поиска изображения.

Формат ответа:
[краткое описание темы новостей]
"""


def generate_image_prompt(post_text: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.5,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": post_text}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Ошибка генерации промпта: {e}")
        return "Financial news and market analysis"
