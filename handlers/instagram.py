import os
import asyncio
import logging
import glob
import requests
import re
from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import States
import yt_dlp

router = Router()

def download_instagram_fast_api(url: str, output_path: str):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        match = re.search(r'/(?:p|reel|reels)/([A-Za-z0-9_-]+)', url)
        if not match:
            return None
        shortcode = match.group(1)
        
        dd_url = f"https://ddinstagram.com/images/{shortcode}/1.mp4"
        r = requests.get(dd_url, headers=headers, stream=True, timeout=15)
        if r.status_code == 200 and len(r.content) > 100000:
            file_name = os.path.join(output_path, f"{shortcode}.mp4")
            with open(file_name, 'wb') as f:
                f.write(r.content)
            return file_name
    except Exception as e:
        logging.error(f"Fast API IG Error: {e}")
    return None

def download_instagram_media(url: str, output_path: str):
    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
        'outtmpl': f'{output_path}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'merge_output_format': 'mp4',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    proxy = os.getenv("HTTP_PROXY") or os.getenv("ALL_PROXY")
    if proxy:
        ydl_opts['proxy'] = proxy

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                file_id = None
                if 'entries' in info and len(info['entries']) > 0:
                    first_entry = info['entries'][0]
                    file_id = first_entry.get('id') if first_entry else None
                else:
                    file_id = info.get('id')
                    
                if file_id:
                    matching_files = glob.glob(f"{output_path}/{file_id}.*")
                    if matching_files:
                        return matching_files[0]
    except Exception as e:
        logging.error(f"yt-dlp Instagram Error: {e}")
                
    return download_instagram_fast_api(url, output_path)

@router.message(F.text == "📥 دانلود اینستاگرام", StateFilter("*"))
async def ig_req(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(States.waiting_for_ig_link)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ انصراف", callback_data="cancel_ig")
    
    await message.answer(
        "🔗 لطفاً لینک پست یا ریلز اینستاگرام را بفرستید:\n(در صورت پشیمانی روی دکمه انصراف کلیک کنید)",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "cancel_ig")
async def cancel_ig(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ دانلود اینستاگرام لغو شد.")
    await callback.answer()

@router.message(States.waiting_for_ig_link)
async def get_ig(message: types.Message, state: FSMContext):
    if message.text and (message.text.startswith("🎵") or message.text.startswith("📥") or message.text.startswith("🔑")):
        await state.clear()
        return

    url = message.text.strip() if message.text else ""
    
    if "instagram.com" not in url or not url.startswith("http"):
        await message.answer("❌ لینک وارد شده معتبر نیست! لطفاً لینک معتبر اینستاگرام بفرستید یا روی انصراف کلیک کنید.")
        return

    status_msg = await message.answer("⏳ در حال دانلود ویدیو از اینستاگرام...")
    
    ig_folder = os.path.join("downloads", "instagram")
    os.makedirs(ig_folder, exist_ok=True)
    
    try:
        file_path = await asyncio.to_thread(download_instagram_media, url, ig_folder)
        
        if file_path and os.path.exists(file_path):
            await status_msg.edit_text("📤 دانلود انجام شد! در حال آپلود به تلگرام...")
            bot_username = (await message.bot.get_me()).username
            
            if file_path.lower().endswith(('.mp4', '.mov', '.m4v', '.webm')):
                await message.answer_video(
                    types.FSInputFile(file_path),
                    caption=f"🎬 <b>خدمت شما!</b>\n\n🤖 @{bot_username}",
                    parse_mode="HTML",
                    request_timeout=600
                )
            else:
                await message.answer_document(
                    types.FSInputFile(file_path),
                    caption=f"📁 <b>خدمت شما!</b>\n\n🤖 @{bot_username}",
                    parse_mode="HTML",
                    request_timeout=600
                )
                
            if os.path.exists(file_path):
                os.remove(file_path)
                
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ خطا در دریافت ویدیو! لطفاً مجدداً تلاش کنید.")

        await state.clear()

    except Exception as e:
        logging.error(f"Instagram Error: {e}")
        await status_msg.edit_text("❌ خطا در آپلود ویدیو!")
        await state.clear()
