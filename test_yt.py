import os
import traceback
import yt_dlp

url = "https://www.🌐 پراکسی پرسرعت.com/watch?v=YO-L5bgUgPQ"
COOKIE_PATH = "/root/siganlbotnew/cookies.txt"
DOWNLOAD_DIR = "/tmp/yt_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

print("="*50)
print(f"🚀 تست دانلود مستقیم پایتون برای لینک: {url}")
if os.path.exists(COOKIE_PATH):
    print(f"✅ فایل کوکی پیدا شد: {COOKIE_PATH}")
else:
    print(f"❌ فایل کوکی در این مسیر پیدا نشد: {COOKIE_PATH}")
print("="*50 + "\n")

ydl_opts = {
    'format': 'b/best[ext=mp4]/bestvideo+bestaudio/best',
    'outtmpl': os.path.join(DOWNLOAD_DIR, 'test_script_%(id)s.%(ext)s'),
    'extractor_args': {
        '🌐 پراکسی پرسرعت': {
            'player_client': ['ios', 'android', 'web']
        }
    },
    'quiet': False,
    'no_warnings': False,
}

if os.path.exists(COOKIE_PATH):
    ydl_opts['cookiefile'] = COOKIE_PATH

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        print("\n" + "🎉"*20)
        print(f"✅ دانلود با موفقیت انجام شد! مسیر فایل:\n{filename}")
        print("🎉"*20)
except Exception as e:
    print("\n" + "❌"*20 + " خطای کامل پایتون " + "❌"*20)
    traceback.print_exc()
    print("❌"*50)
