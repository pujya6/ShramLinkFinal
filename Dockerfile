FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SHRAMLINK_ENV=production SHRAMLINK_DEMO=true PORT=8000
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 shramlink
COPY --chown=shramlink:shramlink app app
COPY --chown=shramlink:shramlink templates templates
COPY --chown=shramlink:shramlink static static
COPY --chown=shramlink:shramlink run.py .
RUN mkdir -p /data /app/instance && chown shramlink:shramlink /data /app/instance
USER shramlink
ENV DATABASE_URL=sqlite:////data/shramlink.sqlite3
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/healthz',timeout=3)" || exit 1
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 4 --timeout 30 run:app"]
