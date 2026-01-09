import os, telebot, subprocess, threading, time
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = '7867778362:AAHtvj9wOAHpG9BPcGPEqNIkT2O5DLXtIPI'
ADMIN_ID = 5747051433
bot = telebot.TeleBot(TOKEN)

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Merge Server Active")

def manage_storage():
    # الاحتفاظ بآخر 5 مقاطع فقط
    files = [f for f in os.listdir('.') if f.endswith('.mp4') and f[:-4].isdigit()]
    files.sort(key=os.path.getctime)
    while len(files) > 5:
        try: os.remove(files.pop(0))
        except: pass

@bot.message_handler(content_types=['document', 'video'])
def handle_files(message):
    caption = message.caption or ""
    if "ID:" in caption:
        try:
            file_id_no = caption.split("ID:")[1].strip()
            # جلب المعرف سواء أرسل كفيديو أو مستند
            file_id = message.document.file_id if message.content_type == 'document' else message.video.file_id
            
            file_info = bot.get_file(file_id)
            downloaded = bot.download_file(file_info.file_path)
            
            file_name = f"{file_id_no}.mp4"
            with open(file_name, "wb") as f:
                f.write(downloaded)
            
            # إرسال إشعار تأكيد لك (مهم جداً)
            bot.send_message(ADMIN_ID, f"📥 تم حفظ المقطع {file_id_no} في الذاكرة.")
            manage_storage()
        except Exception as e:
            print(f"Error: {e}")

@bot.message_handler(commands=['merge'])
def merge_action(message):
    if message.from_user.id != ADMIN_ID: return
    ids = message.text.split()[1:]
    
    # التحقق من وجود الملفات فعلياً في السيرفر
    available = [f[:-4] for f in os.listdir('.') if f.endswith('.mp4')]
    missing = [i for i in ids if i not in available]

    if missing:
        bot.reply_to(message, f"❌ المقاطع {','.join(missing)} غير موجودة.\nالمتوفر حالياً: {','.join(available)}")
        return

    msg = bot.send_message(ADMIN_ID, "⚙️ جاري دمج المقاطع...")
    
    with open('list.txt', 'w') as f:
        for i in ids: f.write(f"file '{i}.mp4'\n")

    output = f"final_{int(time.time())}.mp4"
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', '-y', output])
    
    if os.path.exists(output):
        with open(output, 'rb') as v:
            bot.send_video(ADMIN_ID, v, caption="✅ تم الدمج بنجاح!")
        os.remove(output)
        os.remove('list.txt')
        # حذف المقاطع المدمجة لتوفير مساحة
        for i in ids: 
            try: os.remove(f"{i}.mp4")
            except: pass
    else:
        bot.reply_to(message, "❌ فشل دمج الفيديو.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', port), SimpleHandler).serve_forever(), daemon=True).start()
    bot.polling(non_stop=True)
