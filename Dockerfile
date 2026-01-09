FROM python:3.11-alpine

# تثبيت ffmpeg اللازم للدمج
RUN apk add --no-cache ffmpeg

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# تشغيل ملف البوت
CMD ["python", "merge_bot.py"]
