FROM python:3.12-slim

WORKDIR /app

COPY main.py .

RUN mkdir -p /data

ENV DATA_DIR=/data

CMD ["python", "main.py"]
