import os, telebot, subprocess, threading, time

TOKEN = '7867778362:AAHtvj9wOAHpG9BPcGPEqNIkT2O5DLXtIPI'
REC_BOT_TOKEN = '8001928461:AAEckKw5lfZiQR1cAoLCeSwWoVWIAylj3uc'
ADMIN_ID = 5747051433

bot = telebot.TeleBot(TOKEN)
rec_bot = telebot.TeleBot(REC_BOT_TOKEN)

def manage_storage():
    files = [f for f in os.listdir('.') if f.endswith('.mp4') and f[:-4].isdigit()]
    files.sort(key=os.path.getctime)
    while len(files) > 5:
        try: os.remove(files.pop(0))
        except: pass

@bot.message_handler(content_types=['document'])
def handle_save(message):
    caption = message.caption or ""
    if "SAVE_ID:" in caption:
        try:
            # استخراج الـ ID ورقم الرسالة المراد تعديلها
            parts = caption.split("|")
            save_id = parts[0].split(":")[1]
            msg_id = parts[1].split(":")[1]
            
            # تحميل وحفظ سريع
            file_info = bot.get_file(message.document.file_id)
            downloaded = bot.download_file(file_info.file_path)
            
            with open(f"{save_id}.mp4", "wb") as f:
                f.write(downloaded)
            
            # تعديل رسالة الفيديو الأصلية (عبر توكن بوت التسجيل)
            try:
                rec_bot.edit_message_caption(
                    chat_id=ADMIN_ID, 
                    message_id=int(msg_id), 
                    caption=f"🎥 مقطع {save_id}\n✅ تم الحفظ في الذاكرة بنجاح"
                )
            except: pass
            
            # مسح رسالة المستند من الشات ليبقى الشات نظيفاً
            bot.delete_message(ADMIN_ID, message.message_id)
            
            manage_storage()
        except Exception as e: print(f"Save Error: {e}")

@bot.message_handler(commands=['merge'])
def merge_action(message):
    ids = message.text.split()[1:]
    available = [f[:-4] for f in os.listdir('.') if f.endswith('.mp4')]
    
    with open('list.txt', 'w') as f:
        for i in ids:
            if i in available: f.write(f"file '{i}.mp4'\n")
            else:
                bot.reply_to(message, f"❌ المقطع {i} غير جاهز أو حُذف.")
                return

    output = f"final_{int(time.time())}.mp4"
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', '-y', output])
    
    if os.path.exists(output):
        with open(output, 'rb') as v:
            bot.send_video(ADMIN_ID, v, caption="✅ تم دمج المقاطع المطلوبة!")
        os.remove(output)
        for i in ids: os.remove(f"{i}.mp4")

bot.polling(non_stop=True)
