import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")


def publish_to_telegram(text: str, image_path: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

    with open(image_path, "rb") as photo:
        if len(text) <= 1024:
            data = {"chat_id": TELEGRAM_CHANNEL_ID, "caption": text, "parse_mode": "HTML"}
            files = {"photo": photo}
            response = requests.post(url, data=data, files=files)
        else:
            # Отправляем текст отдельно
            text_data = {
                "chat_id": TELEGRAM_CHANNEL_ID,
                "text": text,
                "parse_mode": "HTML"
            }
            text_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            text_response = requests.post(text_url, data=text_data)
            if not text_response.ok:
                raise RuntimeError(f"❌ Ошибка при отправке текста: {text_response.text}")

            # Потом отправляем фото
            data = {"chat_id": TELEGRAM_CHANNEL_ID}
            files = {"photo": photo}
            response = requests.post(url, data=data, files=files)

    if not response.ok:
        raise RuntimeError(f"❌ Ошибка публикации в Telegram: {response.text}")
