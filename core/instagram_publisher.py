# core/instagram_publisher.py

import os
import requests
from time import sleep
from dotenv import load_dotenv

load_dotenv()

IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")

def publish_to_instagram(image_url: str, caption: str):
    print("📸 Публикуем в Instagram...")

    # 1. Создание media object
    create_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media"
    create_params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    create_resp = requests.post(create_url, data=create_params)
    if create_resp.status_code != 200:
        raise Exception(f"❌ Ошибка создания media объекта: {create_resp.text}")

    creation_id = create_resp.json().get("id")
    print(f"🆔 Media ID: {creation_id}")

    # 2. Публикация media object
    publish_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN
    }

    sleep(5)  # дать IG время подготовить изображение
    publish_resp = requests.post(publish_url, data=publish_params)
    if publish_resp.status_code != 200:
        raise Exception(f"❌ Ошибка публикации в Instagram: {publish_resp.text}")

    print("✅ Пост опубликован в Instagram")