import os, telebot, subprocess, threading, time
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = '7867778362:AAHtvj9wOAHpG9BPcGPEqNIkT2O5DLXtIPI'
ADMIN_ID = 5747051433
bot = telebot.TeleBot(TOKEN)

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Merge Bot is Fully Functional!")

def manage_storage():
    files = [f for f in os.listdir('.') if f.endswith('.mp4') and f[:-4].isdigit()]
    files.sort(key=os.path.getctime)
    while len(files) > 5:
        oldest = files.pop(0)
        try: os.remove(oldest)
        except: pass

@bot.message_handler(content_types=['video'])
def handle_video(message):
    caption = message.caption or ""
    if "ID:" in caption:
        try:
            file_id_number = caption.split("ID:")[1].strip()
            file_info = bot.get_file(message.video.file_id)
            downloaded = bot.download_file(file_info.file_path)
            
            file_name = f"{file_id_number}.mp4"
            with open(file_name, "wb") as f:
                f.write(downloaded)
            
            # إشعار نجاح الحفظ
            bot.send_message(ADMIN_ID, f"✅ تم حفظ المقطع {file_id_number} وهو جاهز للدمج.")
            manage_storage()
        except Exception as e:
            print(f"Error: {e}")

@bot.message_handler(commands=['merge'])
def merge_videos(message):
    if message.from_user.id != ADMIN_ID: return
    ids = message.text.split()[1:]
    if len(ids) < 2:
        bot.reply_to(message, "⚠️ أرسل الأرقام هكذا: /merge 1 2")
        return

    # التحقق من وجود الملفات قبل البدء
    missing = [i for i in ids if not os.path.exists(f"{i}.mp4")]
    if missing:
        bot.reply_to(message, f"❌ المقاطع التالية غير موجودة: {', '.join(missing)}")
        return

    msg = bot.send_message(ADMIN_ID, "⚙️ جاري دمج المقاطع... يرجى الانتظار.")
    
    with open('list.txt', 'w') as f:
        for i in ids: f.write(f"file '{i}.mp4'\n")

    output = f"merged_{int(time.time())}.mp4"
    try:
        # أمر الدمج (Concat)
        result = subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', '-y', output], capture_output=True)
        
        if os.path.exists(output) and os.path.getsize(output) > 0:
            with open(output, 'rb') as v:
                bot.send_video(ADMIN_ID, v, caption="✅ تم الدمج بنجاح!")
            os.remove(output)
            os.remove('list.txt')
            # تنظيف المقاطع التي تم دمجها فقط
            for i in ids: 
                try: os.remove(f"{i}.mp4")
                except: pass
        else:
            bot.edit_message_text("❌ فشل الدمج (خطأ في معالجة FFmpeg).", ADMIN_ID, msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', port), SimpleHandler).serve_forever(), daemon=True).start()
    bot.polling(non_stop=True)
