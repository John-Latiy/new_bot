FROM python:3.12.5-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Ensure entrypoint script is executable
RUN chmod +x /app/entrypoint.sh

# Entrypoint prepares DB/directories, then execs the command
ENTRYPOINT ["/app/entrypoint.sh"]

# By default run the internal scheduler (can be overridden by compose/CLI)
CMD ["python", "-u", "scheduler.py"]