import os
import asyncio
import logging
import glob
import re
import subprocess
import requests
import urllib3
from bs4 import BeautifulSoup
import yt_dlp
from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import States

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
router = Router()

AUDD_API_TOKEN = "b53c2eb718237de9253a1f4b23b36e20"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

# لیست سیاه کامل برای حذف تمامی نسخه‌های غیر اصلی
UNWANTED_KEYWORDS = [
    'remix', 'ریمیکس', 'mix', 'میکس', 'podcast', 'پادکست', 
    'dj', 'دی جی', 'دی‌جی', 'club', 'rework', 'electro', 
    'cover', 'کاور', 'slowed', 'reverb', 'speed up', 'speedup', 'اسپید آپ',
    'acoustic', 'آکوستیک', 'live', 'اجرای زنده', 'زنده',
    'instrumental', 'بی کلام', 'بیکلام', 'بی‌کلام', 'demo', 'دمو',
    'mashup', 'مشاپ', 'mshup', 'drill', 'دریل', 'bass boosted', 'بیس دار', 'بیس‌دار'
]

def is_unwanted_version(text: str, user_query: str) -> bool:
    """بررسی اینکه آیا آهنگ نسخه غیر اصلی است یا خیر"""
    if not text:
        return False
    text_lower = text.lower()
    query_lower = user_query.lower()
    
    for kw in UNWANTED_KEYWORDS:
        # اگر کاربر خودش کلمه خاصی مثل ریمیکس رو سرچ نکرده باشه ولی نتایج داشته باشن، رد میشه
        if kw in text_lower and kw not in query_lower:
            return True
    return False

def convert_ogg_to_mp3(input_path: str, output_path: str) -> bool:
    try:
        command = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-ac', '1',
            '-ar', '44100',
            '-b:a', '128k',
            output_path
        ]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception as e:
        logging.error(f"FFmpeg Convert Error: {e}")
        return False

def recognize_voice_audd(ogg_file_path: str) -> str:
    mp3_path = ogg_file_path.replace('.ogg', '.mp3')
    if not convert_ogg_to_mp3(ogg_file_path, mp3_path):
        mp3_path = ogg_file_path

    try:
        data = {'api_token': AUDD_API_TOKEN, 'return': 'apple_music,spotify'}
        with open(mp3_path, 'rb') as f:
            files = {'file': f}
            response = requests.post('https://api.audd.io/', data=data, files=files, timeout=20, verify=False)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success' and result.get('result'):
                    artist = result['result'].get('artist', '')
                    title = result['result'].get('title', '')
                    rec = f"{artist} {title}".strip()
                    if rec:
                        return rec
    except Exception as e:
        logging.error(f"AudD Exception: {e}")
    finally:
        if os.path.exists(mp3_path) and mp3_path != ogg_file_path:
            try:
                os.remove(mp3_path)
            except Exception:
                pass
    return None

def download_file_direct(url: str, output_path: str) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=30, verify=False)
        if r.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 200000:
                return True
    except Exception as e:
        logging.error(f"Direct Download Error: {e}")
    return False

def search_melobit(query: str, output_folder: str, quality: str = "320"):
    try:
        url = f"https://api-v2.melobit.com/v1/search/query/{requests.utils.quote(query)}/0/15"
        res = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        if res.status_code == 200:
            data = res.json()
            results = data.get('results', [])
            
            selected_song = None
            for item in results:
                if item.get('type') == 'song' and 'song' in item:
                    song = item['song']
                    artist = song['artists'][0].get('fullName', '') if song.get('artists') else ''
                    title_str = f"{artist} - {song.get('title', '')}".strip(" -")
                    
                    if is_unwanted_version(title_str, query):
                        continue
                    
                    selected_song = (song, title_str)
                    break

            if selected_song:
                song, title_str = selected_song
                audio = song.get('audio', {})
                dl_url = None
                if quality == "320":
                    dl_url = (audio.get('high') or {}).get('url') or (audio.get('medium') or {}).get('url')
                else:
                    dl_url = (audio.get('medium') or {}).get('url') or (audio.get('high') or {}).get('url')
                
                if dl_url:
                    file_path = os.path.join(output_folder, f"melobit_{quality}.mp3")
                    if download_file_direct(dl_url, file_path):
                        return file_path, title_str
    except Exception as e:
        logging.error(f"Melobit Error: {e}")
    return None, None

def search_radiojavan(query: str, output_folder: str, quality: str = "320"):
    try:
        search_url = f"https://www.radiojavan.com/api2/search?query={requests.utils.quote(query)}"
        res = requests.get(search_url, headers=HEADERS, timeout=10, verify=False)
        if res.status_code == 200:
            data = res.json()
            mp3s = data.get('mp3s', [])
            
            selected_song = None
            for song in mp3s:
                title_str = f"{song.get('artist', '')} - {song.get('song', '')}".strip(" -")
                if is_unwanted_version(title_str, query):
                    continue
                selected_song = (song, title_str)
                break

            if selected_song:
                song, title_str = selected_song
                song_id = song.get('id')
                q_str = "320" if quality == "320" else "128"
                dl_url = f"https://host2.rj-music.com/media/mp3/mp3-{q_str}/{song_id}.mp3"
                file_path = os.path.join(output_folder, f"rj_{quality}.mp3")
                if download_file_direct(dl_url, file_path):
                    return file_path, title_str
    except Exception as e:
        logging.error(f"RJ Error: {e}")
    return None, None

def search_musicfa(query: str, output_folder: str, quality: str = "320"):
    try:
        search_url = f"https://music-fa.com/?s={requests.utils.quote(query)}"
        res = requests.get(search_url, headers=HEADERS, timeout=10, verify=False)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            articles = soup.find_all('article') or soup.find_all('div', class_='post')
            post_url = None
            for art in articles:
                a_tag = art.find('a', href=True)
                title_text = art.get_text()
                if is_unwanted_version(title_text, query):
                    continue
                if a_tag and 'music-fa.com' in a_tag['href']:
                    post_url = a_tag['href']
                    break
                        
            if post_url:
                post_res = requests.get(post_url, headers=HEADERS, timeout=10, verify=False)
                if post_res.status_code == 200:
                    post_soup = BeautifulSoup(post_res.text, 'html.parser')
                    mp3_links = [l['href'] for l in post_soup.find_all('a', href=True) if l['href'].endswith('.mp3')]
                    
                    if mp3_links:
                        target_q = "320" if quality == "320" else "128"
                        selected_link = next((m for m in mp3_links if target_q in m), mp3_links[0])
                        page_title = query
                        if post_soup.title:
                            page_title = post_soup.title.string.replace("دانلود آهنگ", "").replace("دانلود", "").strip()
                            
                        file_path = os.path.join(output_folder, f"musicfa_{quality}.mp3")
                        if download_file_direct(selected_link, file_path):
                            return file_path, page_title[:40]
    except Exception as e:
        logging.error(f"MusicFa Error: {e}")
    return None, None

def search_soundcloud(query: str, output_folder: str, quality: str = "320"):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{output_folder}/sc_%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': quality}],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch10:{query}", download=False)
            if info and 'entries' in info:
                target_entry = None
                for entry in info['entries']:
                    if not entry:
                        continue
                    t = entry.get('title', '')
                    if is_unwanted_version(t, query):
                        continue
                    target_entry = entry
                    break

                if target_entry:
                    download_info = ydl.extract_info(target_entry['webpage_url'], download=True)
                    file_id = target_entry.get('id')
                    title_str = target_entry.get('title', query)
                    matching = glob.glob(f"{output_folder}/sc_{file_id}.*")
                    if matching:
                        return matching[0], title_str
    except Exception as e:
        logging.error(f"SoundCloud Error: {e}")
    return None, None

def search_and_download_mp3(query: str, output_folder: str, quality: str = "320"):
    # 1. Melobit
    f, t = search_melobit(query, output_folder, quality)
    if f: return f, t

    # 2. RadioJavan
    f, t = search_radiojavan(query, output_folder, quality)
    if f: return f, t

    # 3. MusicFa
    f, t = search_musicfa(query, output_folder, quality)
    if f: return f, t

    # 4. SoundCloud
    f, t = search_soundcloud(query, output_folder, quality)
    if f: return f, t

    return None, None

# -------------------------------------------------------------
# هندلرها
# -------------------------------------------------------------
@router.message(F.text == "🎵 جستجوی آهنگ", StateFilter("*"))
async def music_req(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(States.waiting_for_music_name)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ انصراف", callback_data="cancel_music")
    
    await message.answer(
        "🎵 لطفاً **نام آهنگ/خواننده** را بنویسید یا **قسمتی از وویس/موزیک** را ارسال کنید:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "cancel_music")
async def cancel_music(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ جستجوی آهنگ لغو شد.")
    await callback.answer()

@router.message(States.waiting_for_music_name)
async def process_music_input(message: types.Message, state: FSMContext):
    if message.text and (message.text.startswith("📥") or message.text.startswith("🎵") or message.text.startswith("🔑") or message.text.startswith("☎️")):
        await state.clear()
        return

    music_folder = os.path.join("downloads", "music")
    os.makedirs(music_folder, exist_ok=True)
    query = None

    if message.text:
        query = message.text.strip()
        status_msg = await message.answer(f"🔍 در حال جستجوی نسخه اورجینال: **{query}**...", parse_mode="Markdown")

    elif message.voice or message.audio:
        status_msg = await message.answer("🎧 در حال شناسایی موزیک از روی وویس...")
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        file_info = await message.bot.get_file(file_id)
        
        voice_path = os.path.join(music_folder, f"temp_{message.from_user.id}.ogg")
        await message.bot.download_file(file_info.file_path, voice_path)
        
        recognized_query = await asyncio.to_thread(recognize_voice_audd, voice_path)
        if os.path.exists(voice_path):
            try:
                os.remove(voice_path)
            except Exception:
                pass

        if recognized_query:
            query = recognized_query
        else:
            await status_msg.edit_text("❌ موزیک از روی وویس شناسایی نشد. لطفاً نام آهنگ یا خواننده را به صورت متنی بفرستید.")
            await state.clear()
            return
    else:
        await message.answer("⚠️ لطفاً یک متن (نام آهنگ) یا وویس ارسال کنید.")
        return

    await state.update_data(music_query=query)

    builder = InlineKeyboardBuilder()
    builder.button(text="🔥 کیفیت عالی (320Kbps)", callback_data="dl_320")
    builder.button(text="⚡️ کیفیت متوسط (128Kbps)", callback_data="dl_128")
    builder.button(text="❌ انصراف", callback_data="cancel_music")
    builder.adjust(1)

    await status_msg.edit_text(
        f"✅ موزیک اصلی پیدا شد:\n🎸 <b>{query}</b>\n\nلطفاً کیفیت مد نظر را انتخاب کنید:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.in_({"dl_320", "dl_128"}))
async def download_selected_quality(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    query = user_data.get("music_query")

    if not query:
        await callback.answer("❌ این درخواست منقضی شده است. دوباره تلاش کنید.", show_alert=True)
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    quality = "320" if callback.data == "dl_320" else "128"
    await callback.message.edit_text(f"⏳ در حال دانلود آهنگ اصلی با کیفیت <b>{quality}Kbps</b>...", parse_mode="HTML")
    await callback.answer()

    music_folder = os.path.join("downloads", "music")

    try:
        file_path, title = await asyncio.to_thread(search_and_download_mp3, query, music_folder, quality)
        
        if file_path and os.path.exists(file_path):
            await callback.message.edit_text("📤 در حال آپلود فایل صوتی به تلگرام...")
            bot_username = (await callback.bot.get_me()).username
            
            await callback.message.answer_audio(
                audio=types.FSInputFile(file_path),
                caption=f"🎧 <b>{title or query}</b>\n🎚 کیفیت: {quality}Kbps\n\n🤖 @{bot_username}",
                parse_mode="HTML",
                request_timeout=300
            )
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            await callback.message.delete()
        else:
            await callback.message.edit_text("❌ متأسفانه فایل اصلی پیدا نشد. لطفاً نام دقیق‌تر آهنگ را ارسال کنید.")
            
        await state.clear()

    except Exception as e:
        logging.error(f"Music Handler Error: {e}")
        await callback.message.edit_text("❌ خطا در دانلود موزیک!")
        await state.clear()
