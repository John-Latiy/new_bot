# core/instagram_publisher.py

import os
import requests
from time import sleep
from dotenv import load_dotenv
from utils.image_tools import prepare_for_instagram

load_dotenv()

IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")

def publish_to_instagram(image_url: str, caption: str, local_path: str = None):
    print("📸 Публикуем в Instagram...")

    # Если есть локальный путь, подготовим IG-friendly версию и перезальём на FreeImage
    if local_path and os.path.exists(local_path):
        safe_jpg = prepare_for_instagram(local_path, "data/ig_cover.jpg", variant="portrait")
        # Загрузим обработанный файл на FreeImage.host
        from core.freeimage_uploader import upload_to_freeimage
        image_url = upload_to_freeimage(safe_jpg)

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