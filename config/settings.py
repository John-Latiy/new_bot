import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded from the project root regardless of current working dir
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(DOTENV_PATH)

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Telegram
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

# Instagram
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")

# Image generation
LOGO_PATH = os.getenv("LOGO_PATH")

# FreeImage.host
FREEIMAGE_API_KEY = os.getenv("FREEIMAGE_API_KEY")

# Unsplash (legacy)
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# Image retention (optional)
MAX_COVERS = int(os.getenv("MAX_COVERS", "50"))

# Pixabay
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

