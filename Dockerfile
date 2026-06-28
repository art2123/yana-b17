FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py entrypoint.sh ./
RUN chmod +x entrypoint.sh && mkdir -p /data

ENV DATA_DIR=/data
ENV PYTHONUNBUFFERED=1

CMD ["bash", "entrypoint.sh"]
