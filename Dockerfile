FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY .env.example .

# Thư mục data để mount volume (giữ DB khi restart)
RUN mkdir -p /data
ENV UNIVER_DB_PATH=/data/univer_all_in_one.db

EXPOSE 8443
EXPOSE 8080

CMD ["python", "main.py"]
