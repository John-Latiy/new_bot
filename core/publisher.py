# Публикация в Telegram и Instagram
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")


def publish_to_telegram(text: str, image_path: str):
    import requests
    from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

    url_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    url_text = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Делим текст
    max_caption_len = 1024
    caption = text[:max_caption_len]
    remainder = text[max_caption_len:].strip()

    # 1. Отправляем фото с частью текста
    with open(image_path, 'rb') as photo:
        response = requests.post(url_photo, data={
            "chat_id": TELEGRAM_CHANNEL_ID,
            "caption": caption,
            "parse_mode": "HTML"
        }, files={"photo": photo})

    if not response.ok:
        raise RuntimeError(f"❌ Ошибка публикации фото в Telegram: {response.text}")

    # 2. Если остался хвост — отправляем как отдельное сообщение
    if remainder:
        response = requests.post(url_text, data={
            "chat_id": TELEGRAM_CHANNEL_ID,
            "text": remainder,
            "parse_mode": "HTML"
        })
        if not response.ok:
            raise RuntimeError(f"❌ Ошибка публикации текста в Telegram: {response.text}")
