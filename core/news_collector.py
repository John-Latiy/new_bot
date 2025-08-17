import os
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from config.settings import TELEGRAM_API_ID, TELEGRAM_API_HASH
import sqlite3
from utils.hash_utils import get_hash
import pytz

SESSION_DIR = os.path.join("sessions")
os.makedirs(SESSION_DIR, exist_ok=True)
client = TelegramClient(os.path.join(SESSION_DIR, "parser"), TELEGRAM_API_ID, TELEGRAM_API_HASH)

CHANNELS = [
    "https://t.me/markettwits",
    "https://t.me/thewallstreetpro",
    "https://t.me/if_market_news",
    "https://t.me/moexdiv",
    
]

conn = sqlite3.connect("data/processed.db")
cursor = conn.cursor()

# 🚫 Слова-фильтры рекламы
BAD_WORDS = ["курс", "подпишись", "промокод", "обучение", "трейдинг", "вебинар", "записаться", "тренинг", "морафон","youtube","appstore" ]

def is_advertisement(text: str) -> bool:
    return any(bad_word.lower() in text.lower() for bad_word in BAD_WORDS)

async def fetch_new_posts(start_time=None, end_time=None, limit_per_channel=20):
    new_posts = []

    await client.start()
    for channel in CHANNELS:
        try:
            entity = await client.get_entity(channel)
            history = await client(GetHistoryRequest(
                peer=entity,
                limit=limit_per_channel,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))

            for message in history.messages:
                if not message.message:
                    continue

                message_time = message.date.astimezone(pytz.timezone("Europe/Moscow"))

                # Apply time window filter if provided
                if start_time is not None and end_time is not None:
                    try:
                        if not (start_time <= message_time <= end_time):
                            continue
                    except Exception:
                        # In case of tz-aware mismatches, skip silently
                        continue

                content = message.message.strip()

                # 🔎 Фильтрация рекламы
                if is_advertisement(content):
                    continue  # пропускаем рекламные сообщения

                content_hash = get_hash(content)

                cursor.execute("SELECT 1 FROM processed WHERE message_hash = ?", (content_hash,))
                if cursor.fetchone():
                    continue  # уже обработано

                new_posts.append(content)
                cursor.execute("INSERT INTO processed (message_hash) VALUES (?)", (content_hash,))
                conn.commit()

        except Exception as e:
            print(f"❌ Ошибка при обработке канала {channel}: {e}")

    await client.disconnect()
    return new_posts