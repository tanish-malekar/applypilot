FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /app
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock && python -m playwright install --with-deps chromium
COPY job_agents ./job_agents
COPY examples ./examples
COPY scripts/start-server.py ./scripts/start-server.py
RUN useradd --create-home --uid 1000 app && mkdir -p /app/runtime && chown app:app /app/runtime
USER app
EXPOSE 8000
CMD ["python", "scripts/start-server.py"]
