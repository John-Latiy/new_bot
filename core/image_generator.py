import os
import requests
from openai import OpenAI
from config.settings import OPENAI_API_KEY, UNSPLASH_ACCESS_KEY

# Создаем клиента OpenAI для генерации поисковых запросов
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_search_query(summary: str) -> str:
    """Генерирует поисковый запрос для Unsplash на основе сводки новостей"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.3,
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "Ты помощник для поиска изображений. На основе финансовой сводки "
                        "создай короткий английский поисковый запрос (1-3 слова) для поиска "
                        "подходящего РЕАЛЬНОГО изображения (не AI-generated). Используй общие темы: "
                        "finance, business, stock market, cryptocurrency, economy, banking, money, "
                        "investment, technology, industry. Избегай запросы, которые могут вернуть "
                        "AI-сгенерированные изображения. Отвечай только поисковым запросом."
                    )
                },
                {"role": "user", "content": summary}
            ]
        )
        query = response.choices[0].message.content.strip()
        print(f"🔍 Поисковый запрос для Unsplash: {query}")
        return query
    except Exception as e:
        print(f"❌ Ошибка генерации поискового запроса: {e}")
        return "finance business"

def search_unsplash_image(query: str) -> str:
    """Ищет изображение на Unsplash и возвращает URL"""
    try:
        url = "https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
        params = {
            "query": query,
            "per_page": 10,
            "orientation": "squarish",
            "order_by": "relevant"
        }
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                # Берем первое изображение из результатов
                image_url = data["results"][0]["urls"]["regular"]
                print(f"🖼️ Найдено изображение: {image_url}")
                return image_url
            else:
                print("⚠️ Изображения не найдены, используем запасной вариант")
                return "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1080"
        else:
            raise Exception(f"Ошибка API Unsplash: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка поиска в Unsplash: {e}")
        # Запасное изображение
        return "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1080"

def generate_image(prompt: str, filename: str = "data/final_cover.png") -> str:
    """Ищет изображение на Unsplash вместо генерации через DALL-E"""
    try:
        print(f"🔍 Поиск изображения на Unsplash по теме...")
        
        # Генерируем поисковый запрос на основе промпта
        search_query = generate_search_query(prompt)
        
        # Ищем изображение на Unsplash
        image_url = search_unsplash_image(search_query)
        
        # Загружаем изображение
        print(f"📥 Загружаем изображение...")
        image_data = requests.get(image_url).content
        
        # Сохраняем локально
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as f:
            f.write(image_data)

        print(f"✅ Изображение сохранено: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Ошибка получения изображения: {e}")
        return None