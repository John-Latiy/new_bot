#!/bin/bash

# Переменные
PROJECT_DIR="/Users/evgenijlatij/Desktop/me_code/news_bot"
VENV_PATH="$PROJECT_DIR/venv/bin/activate"
MODE="$1"  # morning / midday / evening

# Лог-файл
LOG_FILE="$PROJECT_DIR/log_${MODE}.txt"

# Активируем виртуальное окружение и запускаем main.py
{
  echo "▶️ Запуск в режиме: $MODE"
  echo "⏰ Время запуска: $(date)"
  source "$VENV_PATH"
  python "$PROJECT_DIR/main.py" --mode "$MODE"
  echo "✅ Завершено в: $(date)"
  echo "---------------------------------------------"
} >> "$LOG_FILE" 2>&1