import os, telebot, subprocess, threading, time
from flask import Flask

TOKEN = '8237586935:AAFCfvGqx5KWuXGwyyECS_flh-V4fulCUGg'
ADMIN_ID = 5747051433
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)
@app.route('/')
def health(): return "OK", 200

@bot.message_handler(func=lambda m: m.caption and "SAVE:" in m.caption, content_types=['document'])
def catch_save(m):
    try:
        fid = m.caption.split(":")[1]
        finfo = bot.get_file(m.document.file_id)
        downloaded = bot.download_file(finfo.file_path)
        with open(f"{fid}.mp4", "wb") as f: f.write(downloaded)
        bot.send_message(ADMIN_ID, f"✅ جاهز {fid}")
        vids = sorted([f for f in os.listdir('.') if f.endswith('.mp4') and f[:-4].isdigit()], key=os.path.getctime)
        while len(vids) > 5: os.remove(vids.pop(0))
        bot.delete_message(ADMIN_ID, m.message_id)
    except: pass

@bot.message_handler(commands=['merge'])
def merge(m):
    ids = m.text.split()[1:]
    with open('list.txt', 'w') as f:
        for i in ids:
            if os.path.exists(f"{i}.mp4"): f.write(f"file '{i}.mp4'\n")
    
    out = f"out_{int(time.time())}.mp4"
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'list.txt', '-c', 'copy', '-y', out])
    
    if os.path.exists(out):
        with open(out, 'rb') as v: bot.send_video(ADMIN_ID, v)
        os.remove(out)
        for i in ids: 
            try: os.remove(f"{i}.mp4")
            except: pass

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))), daemon=True).start()
    bot.polling(non_stop=True)
