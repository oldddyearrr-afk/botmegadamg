import os, telebot, subprocess, threading, time
from flask import Flask

TOKEN = '8237586935:AAFCfvGqx5KWuXGwyyECS_flh-V4fulCUGg'
ADMIN_ID = 5747051433
bot = telebot.TeleBot(TOKEN)

# قاموس لتخزين بيانات المستخدم مؤقتاً
user_data = {}

app = Flask(__name__)
@app.route('/')
def health(): return "Merge Bot is Live", 200

# أمر البدء
@bot.message_handler(commands=['merge'])
def start_merge(message):
    if message.chat.id != ADMIN_ID: return
    user_data[message.chat.id] = {'count': 0, 'files': [], 'step': 'waiting_count'}
    bot.reply_to(message, "🔢 كم عدد المقاطع التي تريد دمجها؟ (أرسل الرقم فقط)")

# استقبال عدد المقاطع
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get('step') == 'waiting_count')
def get_count(message):
    if message.text.isdigit():
        count = int(message.text)
        if count < 2:
            bot.reply_to(message, "⚠️ يجب دمج مقطعين على الأقل. كم العدد؟")
            return
        user_data[message.chat.id]['count'] = count
        user_data[message.chat.id]['step'] = 'waiting_files'
        bot.reply_to(message, f"✅ ممتاز، أرسل المقطع الأول الآن (رقم 1 من {count})")
    else:
        bot.reply_to(message, "❌ يرجى إرسال رقم صحيح.")

# استقبال الفيديوهات
@bot.message_handler(content_types=['video', 'document'], func=lambda m: user_data.get(m.chat.id, {}).get('step') == 'waiting_files')
def get_files(message):
    data = user_data[message.chat.id]
    current_files = data['files']
    
    # تحميل الملف
    bot.send_message(ADMIN_ID, f"📥 جاري تحميل المقطع رقم {len(current_files) + 1}...")
    
    file_id = message.video.file_id if message.content_type == 'video' else message.document.file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    file_path = f"file_{len(current_files)}.mp4"
    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    current_files.append(file_path)
    
    # التحقق هل انتهينا من جمع كل الملفات؟
    if len(current_files) < data['count']:
        bot.reply_to(message, f"👍 تم استلامه. أرسل المقطع رقم {len(current_files) + 1} الآن.")
    else:
        bot.reply_to(message, "🚀 اكتملت المقاطع! جاري البدء في الدمج الفوري بنفس الجودة...")
        user_data[message.chat.id]['step'] = 'merging'
        threading.Thread(target=process_merge, args=(message.chat.id,)).start()

# دالة معالجة الدمج بـ FFmpeg
def process_merge(chat_id):
    files = user_data[chat_id]['files']
    list_path = f"list_{chat_id}.txt"
    output_path = f"final_{chat_id}_{int(time.time())}.mp4"
    
    with open(list_path, 'w') as f:
        for file in files:
            f.write(f"file '{file}'\n")
    
    # دمج بدون إعادة ترميز (نفس الدقة والسرعة)
    cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_path, '-c', 'copy', '-y', output_path]
    subprocess.run(cmd)
    
    if os.path.exists(output_path):
        with open(output_path, 'rb') as final_v:
            bot.send_video(chat_id, final_v, caption="✅ تم الدمج بنجاح!")
    else:
        bot.send_message(chat_id, "❌ حدث خطأ أثناء الدمج.")
    
    # تنظيف الملفات
    for f in files: os.remove(f)
    if os.path.exists(list_path): os.remove(list_path)
    if os.path.exists(output_path): os.remove(output_path)
    del user_data[chat_id]

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))), daemon=True).start()
    bot.polling(non_stop=True)
