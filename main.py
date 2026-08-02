import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import instagram, music, vpn, common, admin, buy
from handlers.proxy import router as proxy_router

logging.basicConfig(level=logging.INFO)

async def main():
    session = AiohttpSession(timeout=600)
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin.router)
    dp.include_router(buy.router)
    dp.include_router(proxy_router)
    dp.include_router(instagram.router)
    dp.include_router(music.router)
    dp.include_router(vpn.router)
    dp.include_router(common.router)

    print("🚀 ربات با تمام روترها و امکانات فعال شد...")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 ربات متوقف شد.")
