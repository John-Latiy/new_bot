# content_factory
ИИ-завод новостей для Telegram и Instagram

## Запуск в Docker

1) Скопируйте `.env.example` в `.env` и заполните ключи (OpenAI, Telegram, Instagram, Pixabay, FreeImage):

2) Соберите и запустите контейнер с встроенным планировщиком (APScheduler):

```
docker compose up --build -d
```

- Образ стартует с `entrypoint.sh`, инициализирует БД (`data/processed.db`) и каталоги, затем запускает `scheduler.py`.
- Время заданий — по Москве (Europe/Moscow). Изменить расписание можно в `scheduler.py`.

3) Логи и данные:
- Логи событий: `logs/post_events.log` (монтируется из хоста)
- База: `data/processed.db` (монтируется из хоста)
- Телеграм-сессии: каталог `sessions/` (монтируется из хоста)

## Ручной запуск без планировщика

Запуск одного прохода:

```
docker compose run --rm new_bot python -u main.py --mode morning
docker compose run --rm new_bot python -u main.py --mode midday
docker compose run --rm new_bot python -u main.py --mode evening
```

## Переменные окружения (.env)

См. `.env.example`. Минимально нужны ключи Telegram, OpenAI, Pixabay и FreeImage.

## Примечания

- Расписание в `scheduler.py` (07:15, 13:15, 23:15 МСК). Изменяйте по необходимости.
- При первом старте создаётся таблица `processed` в `data/processed.db`. Для учёта картинок дополнительно используются таблицы `used_images` и `saved_files` (создаются автоматически).
