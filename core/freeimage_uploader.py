import requests
import os

from dotenv import load_dotenv
load_dotenv()

FREEIMAGE_API_KEY = os.getenv("FREEIMAGE_API_KEY")

def upload_to_freeimage(image_path: str) -> str:
    """
    Загружает изображение на https://freeimage.host и возвращает прямую ссылку.
    """
    print("☁️ Загружаем обложку на FreeImage.host...")

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
        raise Exception(f"❌ Ошибка загрузки на хостинг: {response.text}")