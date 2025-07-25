#!/bin/bash

# Устанавливаем рабочую директорию
PROJECT_DIR="$(cd "$(dirname "$0")"; pwd)"
cd "$PROJECT_DIR"

echo "📁 Текущая директория проекта: $PROJECT_DIR"

# 1. Создание виртуального окружения
echo "🐍 Создание виртуального окружения..."
python3 -m venv venv

# 2. Активация окружения и установка зависимостей
echo "📦 Установка зависимостей..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Делаем run_bot.sh исполняемым
chmod +x "$PROJECT_DIR/run_bot.sh"
echo "✅ Скрипт run_bot.sh сделан исполняемым"

# 4. Добавление cron-задач
echo "🕓 Добавление задач в crontab..."
CRON_JOB_FILE="cron_jobs.txt"

cat > "$CRON_JOB_FILE" <<EOF
# Утро (07:15 по МСК = 14:15 Владивосток)
15 14 * * * $PROJECT_DIR/run_bot.sh morning >> $PROJECT_DIR/log_morning.txt 2>&1

# День (13:15 по МСК = 20:15 Владивосток)
15 20 * * * $PROJECT_DIR/run_bot.sh midday >> $PROJECT_DIR/log_midday.txt 2>&1

# Вечер (23:15 по МСК = 06:15 Владивосток)
15 6 * * * $PROJECT_DIR/run_bot.sh evening >> $PROJECT_DIR/log_evening.txt 2>&1
EOF

crontab "$CRON_JOB_FILE"
rm "$CRON_JOB_FILE"
echo "✅ Cron задачи установлены"

echo "🎉 Установка завершена!"