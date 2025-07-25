import argparse
import asyncio

from utils.time_windows import get_time_range_for_mode
from core.news_collector import fetch_new_posts
from core.text_processor import generate_summary
from core.image_prompt_generator import generate_image_prompt
from core.image_generator import generate_image
from core.publisher import publish_to_telegram
from core.instagram_publisher import publish_to_instagram
from core.freeimage_uploader import upload_to_freeimage


def parse_args():
    parser = argparse.ArgumentParser(description="News Publisher Bot")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["morning", "midday", "evening"],
        help="Mode of the day"
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    mode = args.mode

    print(f"\n🔄 Режим запуска: {mode}")
    start_time, end_time = get_time_range_for_mode(mode)
    print(f"🕒 Временной диапазон по Москве: {start_time} → {end_time}\n")

    # Сбор новостей
    raw_posts = await fetch_new_posts(
        start_time,
        end_time,
        limit_per_channel=10
    )
    if not raw_posts:
        print("⚠️ Нет новостей за указанный период.")
        return

    # Генерация текста
    print("📝 GPT формирует связную сводку...")
    try:
        summary = generate_summary(raw_posts)
        print(f"\n📢 Сформированная сводка:\n\n{summary}\n")
    except Exception as e:
        print(f"⚠️ Ошибка генерации сводки: {e}\n")
        return

    # Генерация промпта для изображения
    print("🎨 Генерация промпта...")
    disclaimer = "(This image is for informational and artistic purposes only. It does not promote violence, politics, or any sensitive content.) "
    prompt = disclaimer + generate_image_prompt(summary)
    print(f"\n🧠 GPT промпт:\n{prompt}\n")

    # Генерация изображения
    image_path = "data/final_cover.png"
    print("\n🖼 ️Генерация обложки...")
    try:
        image_path = generate_image(prompt)
        print(f"✅ Обложка сохранена: {image_path}\n")
    except Exception as e:
        print(f"❌ Ошибка генерации обложки, прерывание публикации.\n{e}")
        return

    # Загрузка изображения на FreeImage.host
    try:
        print("☁️ Загружаем обложку на FreeImage.host...")
        image_url = upload_to_freeimage(image_path)
        print(f"🔗 Ссылка на изображение: {image_url}\n")
    except Exception as e:
        print(f"❌ Ошибка загрузки на хостинг: {e}")
        return

    # Публикация в Telegram
    print("📣 Публикация в Telegram...")
    try:
        publish_to_telegram(summary, image_path)
        print("✅ Пост опубликован в Telegram")
    except Exception as e:
        print(f"❌ Ошибка публикации в Telegram: {e}")

    # Публикация в Instagram
    print("📸 Публикация в Instagram...")
    try:
        publish_to_instagram(image_url, summary)
        print("✅ Пост опубликован в Instagram")
    except Exception as e:
        print(f"❌ Ошибка публикации в Instagram: {e}")


if __name__ == "__main__":
    asyncio.run(main())