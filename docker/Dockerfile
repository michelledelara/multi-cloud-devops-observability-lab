FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 lab \
    && useradd --uid 10001 --gid lab --no-create-home lab \
    && mkdir -p /var/log/lab \
    && chown -R 10001:10001 /var/log/lab
COPY --chown=10001:10001 app ./app
USER 10001:10001
EXPOSE 8080
# One process keeps the in-memory Prometheus registry consistent; scale with Pods.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--worker-tmp-dir", "/tmp", "--timeout", "15", "app.main:app"]
