import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Router, F
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

CHANNEL_USERNAME = "@v2rayconfigamo"

sub_router = Router()

@sub_router.callback_query(F.data == "check_sub_again")
async def check_sub_again_handler(callback: CallbackQuery):
    bot = callback.bot
    user_id = callback.from_user.id
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            await callback.message.edit_text("✅ **عضویت شما تأیید شد!**\n\nحالا می‌توانید از تمامی امکانات ربات استفاده کنید.")
            await callback.answer("✅ عضویت تأیید شد!", show_alert=True)
            return
    except Exception as e:
        logging.error(f"Check sub callback error: {e}")
        
    await callback.answer("❌ شما هنوز در کانال عضو نشده‌اید!", show_alert=True)

class CheckSubMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # تمام کلیک روی دکمه‌ها عبور داده می‌شوند تا هیچ دکمه‌ای روی لودینگ نماند
        if isinstance(event, CallbackQuery):
            return await handler(event, data)

        if isinstance(event, Message):
            user = event.from_user
            if not user:
                return await handler(event, data)

            bot = data.get("bot")
            try:
                member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user.id)
                if member.status in ["member", "administrator", "creator"]:
                    return await handler(event, data)
            except Exception as e:
                logging.error(f"CheckSubMiddleware Error: {e}")
                return await handler(event, data)

            channel_clean = CHANNEL_USERNAME.replace('@', '')
            channel_link = f"https://t.me/{channel_clean}"
            
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 عضویت در کانال رسمی", url=channel_link)],
                [InlineKeyboardButton(text="🔄 بررسی مجدد عضویت", callback_data="check_sub_again")]
            ])

            text = (
                "⚠️ **دسترسی محدود شده است!**\n\n"
                "برای استفاده از تمامی قابلیت‌های ربات، ابتدا باید در کانال رسمی ما عضو شوید:\n"
                f"👉 {CHANNEL_USERNAME}\n\n"
                "پس از عضویت، روی دکمه **«🔄 بررسی مجدد عضویت»** کلیک کنید."
            )

            await event.answer(text, reply_markup=kb, parse_mode="Markdown")
            return

        return await handler(event, data)
