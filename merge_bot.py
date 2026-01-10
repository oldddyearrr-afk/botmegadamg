import os, telebot, subprocess, threading, time
from flask import Flask

TOKEN = '8237586935:AAFCfvGqx5KWuXGwyyECS_flh-V4fulCUGg'
ADMIN_ID = 5747051433
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)
@app.route('/')
def health(): return "Merge Bot Online", 200

@bot.message_handler(func=lambda m: m.caption and "SAVE:" in m.caption, content_types=['document'])
def catch_save(m):
    try:
        fid = m.caption.split(":")[1]
        finfo = bot.get_file(m.document.file_id)
        downloaded = bot.download_file(finfo.file_path)
        with open(f"{fid}.mp4", "wb") as f: f.write(downloaded)
        bot.send_message(ADMIN_ID, f"✅ تم استلام المقطع {fid} وحفظه.")
        # تنظيف تلقائي
        vids = sorted([f for f in os.listdir('.') if f.endswith('.mp4') and f[:-4].isdigit()], key=os.path.getctime)
        while len(vids) > 10: os.remove(vids.pop(0))
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ خطأ أثناء الحفظ: {e}")

@bot.message_handler(commands=['merge'])
def merge(m):
    if m.chat.id != ADMIN_ID: return
    
    ids = m.text.split()[1:]
    if not ids:
        bot.reply_to(m, "⚠️ يرجى كتابة الأرقام، مثال:\n/merge 1 2")
        return

    bot.reply_to(m, f"⚙️ جاري محاولة دمج {len(ids)} مقاطع...")
    
    available_files = []
    for i in ids:
        file_path = f"{i}.mp4"
        if os.path.exists(file_path):
            available_files.append(file_path)
        else:
            bot.send_message(ADMIN_ID, f"❓ المقطع {i} غير موجود في السيرفر.")

    if len(available_files) < 2:
        bot.send_message(ADMIN_ID, "❌ لا يمكن الدمج، أحتاج لمقطعين على الأقل موجودين بالسيرفر.")
        return

    with open('list.txt', 'w') as f:
        for f_path in available_files:
            f.write(f"file '{f_path}'\n")
    
    out = f"final_video_{int(time.time())}.mp4"
    try:
        # تنفيذ FFmpeg مع التقاط الخطأ إن وجد
        result = subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', '-y', out], capture_output=True, text=True)
        
        if os.path.exists(out) and os.path.getsize(out) > 0:
            with open(out, 'rb') as v:
                bot.send_video(ADMIN_ID, v, caption="✅ تم الدمج بنجاح!")
            os.remove(out)
            # مسح الملفات المدمجة فقط
            for f_path in available_files: os.remove(f_path)
        else:
            bot.send_message(ADMIN_ID, f"❌ فشل FFmpeg في إنتاج الفيديو:\n{result.stderr[:100]}")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ خطأ برمي: {e}")
    finally:
        if os.path.exists('list.txt'): os.remove('list.txt')

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))), daemon=True).start()
    bot.polling(non_stop=True)
