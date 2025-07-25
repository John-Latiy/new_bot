import os
import requests
from time import sleep

# Настройки
IMAGE_PATH = "data/final_cover.png"
CAPTION = "💹 Тестовая публикация в Instagram через FreeImage.host"
IG_USER_ID = "17841470355080685"  # Твой IG user ID
# IG_ACCESS_TOKEN = "EAAPawYyoSuIBO9oCQ6BM7ZByuvcroIBWi7h9bjSBGXIR4AC6dcTUlfVREjJLrIQkruusgIisPwgBJEKNCl4Yvs0HYhRhkSAGcwZCdBmLwigLqCJUr0bo4uK0ArKIfgejk2EnQq0QMLShuCu4FS8rFGdRTM8XiPvuRhG4jtArjJLjX0GayevVNjYpmeeh1qLHJbAw5RCC1I"
FREEIMAGE_API_KEY = "6d207e02198a847aa98d0a2a901485a5"


def upload_to_freeimage(image_path: str) -> str:
    print("📤 Загружаем изображение на FreeImage.host...")

    api_url = "https://freeimage.host/api/1/upload"
    with open(image_path, "rb") as f:
        files = {"source": f}
        data = {
            "key": FREEIMAGE_API_KEY,
            "action": "upload",
            "format": "json"
        }
        response = requests.post(api_url, files=files, data=data)

    if response.status_code == 200:
        json_data = response.json()
        if "image" in json_data and "url" in json_data["image"]:
            image_url = json_data["image"]["url"]
            print(f"🔗 Ссылка на изображение: {image_url}")
            return image_url
        else:
            raise Exception(f"❌ Ошибка: неожиданный формат ответа: {response.text}")
    else:
        raise Exception(f"❌ Ошибка загрузки: {response.text}")


def publish_to_instagram(image_url: str, caption: str):
    print("📸 Публикуем в Instagram...")

    # Шаг 1: создаем media object
    create_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media"
    create_params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    create_resp = requests.post(create_url, data=create_params)
    if create_resp.status_code != 200:
        raise Exception(f"❌ Ошибка создания media object: {create_resp.text}")

    creation_id = create_resp.json()["id"]
    print(f"🆔 Media ID: {creation_id}")

    # Шаг 2: публикуем media object
    publish_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN
    }
    sleep(5)  # небольшой таймаут, чтобы IG успел подготовить медиа
    publish_resp = requests.post(publish_url, data=publish_params)
    if publish_resp.status_code != 200:
        raise Exception(f"❌ Ошибка публикации: {publish_resp.text}")

    print("✅ Пост опубликован в Instagram")


if __name__ == "__main__":
    image_url = upload_to_freeimage(IMAGE_PATH)
    publish_to_instagram(image_url, CAPTION)
