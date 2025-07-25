# core/image_prompt_generator.py

from openai import OpenAI
from config.settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Ты — профессиональный AI-художник, создающий визуальные обложки для постов о финансах, экономике, криптовалютах и фондовом рынке.

На основе текста поста ты должен придумать красивый, атмосферный, насыщенный визуальный промпт для генерации изображения в стиле DALL·E 3.

Не пиши текст на изображении. Используй конкретику: графики, фонды, доллар, банк, завод, спутник, монеты, фондовый рынок, нефть, здание ЦБ — то, что визуально покажет суть новости. Придерживайся художественного и современного стиля. Обязательно указывай: “no text, no words, no captions”.

Формат ответа:
[только строка-промпт для DALL·E 3]
"""

def generate_image_prompt(post_text: str) -> str:
    disclaimer = "(This image is for informational and artistic purposes only. It does not promote violence, politics, or any sensitive content.) "
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.8,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": disclaimer + post_text}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Ошибка генерации промпта: {e}")
        return "Abstract finance chart with blue-orange colors, no text"
