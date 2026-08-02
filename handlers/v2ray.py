import logging
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# آدرس کانال خود را اینجا وارد کنید (مثلاً @your_channel)
CHANNEL_USERNAME = "@your_channel_username" 

async def check_user_membership(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception as e:
        logging.error(f"Membership check error: {e}")
    return False

@router.message(F.text == "🔑 دریافت کانفیگ V2Ray")
async def get_v2ray_config(message: types.Message):
    user_id = message.from_user.id
    is_member = await check_user_membership(message.bot, user_id)
    
    if not is_member:
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
        builder.button(text="🔄 بررسی عضویت", callback_data="check_membership_v2ray")
        builder.adjust(1)
        
        await message.answer(
            "⚠️ برای دریافت کانفیگ V2Ray، لطفاً ابتدا در کانال ما عضو شوید و سپس روی دکمه بررسی عضویت بزنید:",
            reply_markup=builder.as_markup()
        )
        return

    # منطق ارسال کانفیگ V2Ray به کاربر
    await message.answer("✅ این هم کانفیگ V2Ray اختصاصی شما...")

@router.callback_query(F.data == "check_membership_v2ray")
async def check_membership_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_member = await check_user_membership(callback.bot, user_id)
    
    if is_member:
        await callback.message.edit_text("✅ عضویت شما تأیید شد! حالا می‌توانید مجدداً روی دکمه دریافت کانفیگ بزنید.")
    else:
        await callback.answer("❌ شما هنوز در کانال عضو نشده‌اید!", show_alert=True)
