import os, telebot, subprocess, threading, time
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- إعدادات بوت الدمج ---
TOKEN = '7867778362:AAHtvj9wOAHpG9BPcGPEqNIkT2O5DLXtIPI'
ADMIN_ID = 5747051433
bot = telebot.TeleBot(TOKEN)

# خادم وهمي لإبقاء السيرفر "Live" على Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Merge Bot (Rolling Buffer) is Active!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# --- دالة إدارة المساحة (حذف الأقدم إذا تجاوز 5 مقاطع) ---
def manage_storage():
    # جلب قائمة الملفات التي تبدأ برقم وتنتهي بـ .mp4 وترتيبها حسب وقت الإنشاء
    files = [f for f in os.listdir('.') if f.endswith('.mp4') and f[0].isdigit()]
    files.sort(key=os.path.getctime) # الأقدم أولاً
    
    while len(files) > 5:
        oldest_file = files.pop(0)
        try:
            os.remove(oldest_file)
            print(f"🗑️ تم حذف المقطع القديم لتوفير مساحة: {oldest_file}")
        except: pass

# --- استقبال وحفظ المقاطع تلقائياً ---
@bot.message_handler(content_types=['video'])
def handle_incoming_video(message):
    caption = message.caption or ""
    if "ID:" in caption:
        try:
            file_id_number = caption.split("ID:")[1].strip()
            
            # تحميل المقطع
            file_info = bot.get_file(message.video.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # حفظ المقطع الجديد
            file_name = f"{file_id_number}.mp4"
            with open(file_name, "wb") as f:
                f.write(downloaded_file)
            
            print(f"📥 تم حفظ المقطع الجديد ID: {file_id_number}")
            
            # إدارة المساحة: حذف الأقدم فوراً إذا تجاوز العدد 5
            manage_storage()
            
        except Exception as e:
            print(f"Error: {e}")

# --- أمر الدمج: مثال /merge 2 3 4 5 6 ---
@bot.message_handler(commands=['merge'])
def merge_videos(message):
    if message.from_user.id != ADMIN_ID: return
    
    ids = message.text.split()[1:]
    if len(ids) < 2:
        bot.reply_to(message, "⚠️ أرسل أرقام المقاطع المتوفرة حالياً، مثال: /merge 2 3 4")
        return

    bot.send_message(ADMIN_ID, f"⚙️ جاري دمج المقاطع المطلوبة...")

    with open('list.txt', 'w') as f:
        valid_files = []
        for i in ids:
            fname = f"{i}.mp4"
            if os.path.exists(fname):
                f.write(f"file '{fname}'\n")
                valid_files.append(fname)
            else:
                bot.send_message(ADMIN_ID, f"❌ المقطع رقم {i} غير موجود (ربما تم حذفه لأنه قديم جداً)!")
                return

    output_file = "final_output.mp4"
    
    try:
        subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', '-y', output_file], check=True)

        if os.path.exists(output_file):
            with open(output_file, 'rb') as v:
                bot.send_video(ADMIN_ID, v, caption="✅ المقطع المدمج (آخر التحديثات)!")
            
            # تنظيف ملفات الدمج فقط، ونترك المقاطع الأصلية إذا كانت ضمن الـ 5 الأخيرة
            os.remove(output_file)
            os.remove('list.txt')
        else:
            bot.reply_to(message, "❌ فشل الدمج.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    print("🚀 بوت الدمج الذكي يعمل بنظام الـ 5 مقاطع الأخيرة...")
    bot.polling(non_stop=True)
