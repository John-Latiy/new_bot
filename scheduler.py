# scheduler.py

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
import pytz

def run_job(mode):
    print(f"🕒 Запуск задачи для режима: {mode}")
    subprocess.run(["python", "main.py", "--mode", mode])

tz = pytz.timezone("Europe/Moscow")
scheduler = BlockingScheduler(timezone=tz)

# Утренний пост — 07:15 по Москве
scheduler.add_job(run_job, CronTrigger(hour=7, minute=15), args=["morning"], name="morning_news")

# Дневной пост — 13:15 по Москве
scheduler.add_job(run_job, CronTrigger(hour=13, minute=15), args=["midday"], name="midday_news")

# Вечерний пост — 23:15 по Москве
scheduler.add_job(run_job, CronTrigger(hour=23, minute=15), args=["evening"], name="evening_news")

print("⏳ Планировщик запущен... Ждём следующего запуска.")
scheduler.start()
