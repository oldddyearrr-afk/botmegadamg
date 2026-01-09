import os, telebot, subprocess, threading, time
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- الإعدادات ---
TOKEN = '7867778362:AAHtvj9wOAHpG9BPcGPEqNIkT2O5DLXtIPI'
ADMIN_ID = 5747051433
bot = telebot.TeleBot(TOKEN)

# خادم وهمي لإبقاء السيرفر حياً
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Merge Bot is Active and Listening...")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), SimpleHandler).serve_forever()

# --- نظام إدارة الـ 5 مقاطع الأخيرة ---
def manage_storage():
    # جلب الملفات التي أسماؤها أرقام (ID)
    files = [f for f in os.listdir('.') if f.endswith('.mp4') and f[:-4].isdigit()]
    # ترتيب حسب وقت الإنشاء (الأقدم أولاً)
    files.sort(key=lambda x: os.path.getctime(x))
    
    while len(files) > 5:
        oldest = files.pop(0)
        try:
            os.remove(oldest)
            print(f"🗑️ Deleted oldest file: {oldest}")
        except: pass

# --- استقبال الفيديوهات (منك أو التي يرسلها البوت لنفسه) ---
@bot.message_handler(content_types=['video'])
def handle_video(message):
    caption = message.caption or ""
    # نبحث عن كلمة ID: في الوصف
    if "ID:" in caption:
        try:
            # استخراج الرقم من الكابشن
            file_id_no = caption.split("ID:")[1].strip()
            
            # تحميل الملف من تليجرام
            file_info = bot.get_file(message.video.file_id)
            downloaded = bot.download_file(file_info.file_path)
            
            # حفظ الملف باسم الرقم (مثلاً 1.mp4)
            file_name = f"{file_id_no}.mp4"
            with open(file_name, "wb") as f:
                f.write(downloaded)
            
            # إرسال تأكيد لك (حتى تطمئن أن الملف صار بالسيرفر)
            bot.send_message(ADMIN_ID, f"✅ تم حفظ المقطع {file_id_no} في الذاكرة.")
            
            # إدارة المساحة (حذف الأقدم إذا تجاوزوا 5)
            manage_storage()
        except Exception as e:
            print(f"Error saving: {e}")

# --- أمر الدمج: مثال /merge 1 2 3 ---
@bot.message_handler(commands=['merge'])
def merge_action(message):
    if message.from_user.id != ADMIN_ID: return
    
    ids = message.text.split()[1:]
    if len(ids) < 2:
        bot.reply_to(message, "⚠️ يرجى كتابة الأرقام، مثال: /merge 1 2")
        return

    # التأكد من وجود الملفات المطلوبة
    valid_files = []
    missing_files = []
    for i in ids:
        if os.path.exists(f"{i}.mp4"):
            valid_files.append(f"{i}.mp4")
        else:
            missing_files.append(i)

    if missing_files:
        bot.reply_to(message, f"❌ المقاطع التالية غير موجودة: {', '.join(missing_files)}\n(ربما تم حذفها لأنها قديمة)")
        return

    bot.send_message(ADMIN_ID, f"⚙️ جاري دمج {len(valid_files)} مقاطع...")

    # إنشاء قائمة الدمج لـ FFmpeg
    with open('list.txt', 'w') as f:
        for vid in valid_files:
            f.write(f"file '{vid}'\n")

    output = f"result_{int(time.time())}.mp4"
    
    try:
        # عملية الدمج السريع
        subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', '-y', output], check=True)
        
        if os.path.exists(output):
            with open(output, 'rb') as v:
                bot.send_video(ADMIN_ID, v, caption="✅ إليك المقطع المدمج!")
            
            # تنظيف ملفات الدمج
            os.remove(output)
            os.remove('list.txt')
            # اختياري: إذا أردت حذف الأصول بعد الدمج فوراً
            for f in valid_files:
                try: os.remove(f)
                except: pass
        else:
            bot.reply_to(message, "❌ فشل دمج الملفات.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ تقني: {e}")

if __name__ == "__main__":
    # تشغيل السيرفر في خيط منفصل
    threading.Thread(target=run_server, daemon=True).start()
    print("🚀 Merge Bot is Starting...")
    # ملاحظة: allowed_updates تجعل البوت يرى كل أنواع الرسائل
    bot.polling(non_stop=True, allowed_updates=["message", "edited_message", "channel_post"])
