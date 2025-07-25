import os
import openai
import requests
from config.settings import OPENAI_API_KEY

# Создаем клиента
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def generate_image(prompt: str, filename: str = "data/final_cover.png") -> str:
    try:
        print(f"[DEBUG] 🔹 Генерация изображения по промпту:\n{prompt}\n[no text, no words, no captions]")

        # Новый синтаксис OpenAI >=1.0.0
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            n=1
        )

        image_url = response.data[0].url
        print(f"[DEBUG] 🔹 Ссылка на изображение: {image_url}")

        image_data = requests.get(image_url).content
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as f:
            f.write(image_data)

        print(f"[DEBUG] ✅ Изображение сохранено: {filename}")
        return filename
    except Exception as e:
        print(f"❌ [ERROR] Ошибка генерации изображения:\n{e}")
        return None