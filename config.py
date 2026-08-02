import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

API_TOKEN = "GirYBXjjzCmkbgc4JAXE7uZSrikNN4buNtnuOUqRTAKAu3sp" 

ADMIN_USERNAMES = ["kiamasoomi"]  
ADMIN_IDS = [5460246144]  
SUPPORT_ID = 5460246144

BOT_TOKEN = "8847726470:AAEvVvCcfuR9QeRlgzVg0EdOWL42dIjqnAU"
TOKEN = BOT_TOKEN

CHANNEL_ID = "@v2rayconfigamo"  
CARD_INFO = "6037/7019/0564/8603 - کسری معصومی"

BASE_URL = "https://127.0.0.1:5379/YY6y6LwMYl9NxSt20H"
XUI_USER = "amo"
XUI_PASS = "sinakasra"  

INBOUND_TEST = 5  
INBOUND_BUY = 6   

PRICES = {
    "10": "100,000",
    "15": "150,000",
    "20": "200,000"
}

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def check_and_update_admin(user):
    if user and user.username:
        if user.username.lower() in [u.lower() for u in ADMIN_USERNAMES]:
            if user.id not in ADMIN_IDS:
                ADMIN_IDS.append(user.id)
