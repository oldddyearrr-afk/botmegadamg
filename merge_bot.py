import os, telebot, subprocess, threading, time
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- الإعدادات ---
TOKEN = '8237586935:AAFCfvGqx5KWuXGwyyECS_flh-V4fulCUGg'
ADMIN_ID = 5747051433
bot = telebot.TeleBot(TOKEN)

# دالة لتنظيف السيرفر (آخر 5 فقط)
def manage_storage():
    vids = [f for f in os.listdir('.') if f.endswith('.mp4') and f[:-4].isdigit()]
    vids.sort(key=os.path.getctime)
    while len(vids) > 5:
        try: os.remove(vids.pop(0))
        except: pass

# --- "الصياد" لالتقاط الملفات وحفظها في السيرفر ---
@bot.message_handler(func=lambda m: m.caption and "SAVE:" in m.caption, content_types=['document', 'video'])
def catch_and_save(message):
    try:
        file_id_no = message.caption.split(":")[1]
        # سحب الملف سواء كان مستند أو فيديو
        f_id = message.document.file_id if message.content_type == 'document' else message.video.file_id
        
        file_info = bot.get_file(f_id)
        downloaded = bot.download_file(file_info.file_path)
        
        # الحفظ الفيزيائي في سيرفر Render
        with open(f"{file_id_no}.mp4", "wb") as f:
            f.write(downloaded)
        
        # إشعار نجاح الحفظ
        bot.send_message(ADMIN_ID, f"✅ تم حفظ المقطع {file_id_no} وهو جاهز للدمج الآن.")
        manage_storage()
        
        # مسح رسالة المستند ليبقى الشات نظيفاً (اختياري)
        bot.delete_message(ADMIN_ID, message.message_id)
        
    except Exception as e:
        print(f"Save Error: {e}")

# --- أمر الدمج ---
@bot.message_handler(commands=['merge'])
def merge_files(message):
    ids = message.text.split()[1:]
    available = [f[:-4] for f in os.listdir('.') if f.endswith('.mp4')]
    
    # التأكد من أن كل الأرقام المطلوبة موجودة في السيرفر
    for i in ids:
        if i not in available:
            bot.reply_to(message, f"❌ المقطع {i} غير موجود في ذاكرة السيرفر.\nالموجود: {available}")
            return

    bot.send_message(ADMIN_ID, "⚙️ جاري دمج المقاطع المطلوبة...")
    
    with open('list.txt', 'w') as f:
        for i in ids: f.write(f"file '{i}.mp4'\n")
    
    output = f"final_{int(time.time())}.mp4"
    # عملية الدمج باستخدام FFmpeg
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', '-y', output])
    
    if os.path.exists(output):
        with open(output, 'rb') as v:
            bot.send_video(ADMIN_ID, v, caption="✅ تم الدمج بنجاح!")
        os.remove(output)
        os.remove('list.txt')
        # مسح المقاطع الأصلية بعد الدمج لتوفير مساحة
        for i in ids: os.remove(f"{i}.mp4")

if __name__ == "__main__":
    # تشغيل خادم وهمي لمنع Render من إغلاق السيرفر
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 8080), lambda *a,**k: None).serve_forever(), daemon=True).start()
    bot.polling(non_stop=True)
