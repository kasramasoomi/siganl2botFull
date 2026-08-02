import sqlite3
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

class States(StatesGroup):
    waiting_for_name = State()
    waiting_for_receipt = State()
    waiting_for_movie_name = State()
    waiting_for_ig_link = State()
    waiting_for_music_name = State()

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS testers (user_id INTEGER PRIMARY KEY)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            gb TEXT,
            photo_file_id TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()

def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🌐 پراکسی تلگرام")
    kb.button(text="📥 دانلود اینستاگرام")
    kb.button(text="🎵 جستجوی آهنگ")
    kb.button(text="🔑 خدمات VPN")
    kb.button(text="👨‍💻 پشتیبانی")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

def plan_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔹 10 گیگابایت - 100,000 تومان", callback_data="buy_10")
    kb.button(text="🔹 15 گیگابایت - 150,000 تومان", callback_data="buy_15")
    kb.button(text="🔹 20 گیگابایت - 200,000 تومان", callback_data="buy_20")
    kb.adjust(1)
    return kb.as_markup()
