FROM python:3.11-slim

# تثبيت FFmpeg وتحديث النظام
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ الملفات وتثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# تشغيل البوت (تأكد أن اسم الملف هو merge_bot.py في بوت الدمج و main.py في التسجيل)
CMD ["python", "merge_bot.py"]
