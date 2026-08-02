import logging
import sqlite3
import re
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.vpn import create_xui_config
try:
    from config import INBOUND_BUY
except ImportError:
    INBOUND_BUY = 6

router = Router()
SUPPORT_USERNAME = "kiamasoomi"

# فیلتر اختصاصی برای دکمه‌های app_ و rej_
@router.callback_query(F.data.startswith("app_") | F.data.startswith("rej_"))
async def process_receipt(callback: types.CallbackQuery):
    data = callback.data
    
    if data.startswith("app_"):
        action = "approve"
        receipt_id = data.replace("app_", "")
    else:
        action = "reject"
        receipt_id = data.replace("rej_", "")

    # استخراج اطلاعات فیش از دیتابیس users.db
    user_id = None
    gb = None
    full_name = "کاربر"

    try:
        conn = sqlite3.connect("/root/siganlbotnew/users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, gb, full_name FROM receipts WHERE rowid = ?", (receipt_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            user_id, gb, full_name = row[0], row[1], row[2]
    except Exception as e:
        logging.error(f"Database error: {e}")

    if not user_id:
        await callback.answer("❌ اطلاعات فیش در دیتابیس پیدا نشد!", show_alert=True)
        return

    await callback.answer()

    # ------------------ 1. تایید فیش و ساخت کانفیگ ------------------
    if action == "approve":
        try:
            status_reply = await callback.message.reply("⏳ در حال ساخت کانفیگ روی اینباند خرید...")
            
            # ساخت کانفیگ روی اینباند خرید (شناسه 6)
            config_link, err_msg = await create_xui_config(
                inbound_id=INBOUND_BUY,
                user_name=full_name or f"User_{user_id}",
                gb_limit=gb,
                days=30
            )

            await status_reply.delete()

            if config_link:
                # ارسال پیام و لینک کانفیگ به کاربر
                text_user = (
                    f"✅ <b>رسید پرداخت شما ({gb} گیگابایت) با موفقیت تأیید شد!</b>\n\n"
                    f"🔑 <b>لینک کانفیگ اختصاصی شما:</b>\n"
                    f"<code>{config_link}</code>\n\n"
                    f"📌 <i>جهت کپی کردن، روی کد بالا لمس کنید.</i>"
                )
                await callback.bot.send_message(
                    chat_id=user_id,
                    text=text_user,
                    parse_mode="HTML"
                )

                # پاک کردن دکمه‌ها و اطلاع به ادمین
                await callback.message.edit_reply_markup(reply_markup=None)
                await callback.message.reply(
                    f"✅ <b>فیش شماره {receipt_id} تأیید شد.\nکانفیگ {gb} گیگابایت روی اینباند {INBOUND_BUY} ساخته شد و برای کاربر <code>{user_id}</code> ارسال گردید.</b>",
                    parse_mode="HTML"
                )
            else:
                await callback.message.reply(
                    f"❌ <b>خطا در ساخت کانفیگ در پنل:</b>\n<code>{err_msg}</code>",
                    parse_mode="HTML"
                )

        except Exception as e:
            await callback.message.reply(f"❌ خطا در پردازش تأیید ({user_id}):\n<code>{e}</code>", parse_mode="HTML")

    # ------------------ 2. رد فیش ------------------
    elif action == "reject":
        try:
            builder = InlineKeyboardBuilder()
            builder.button(text="🎧 ارتباط با پشتیبانی", url=f"https://t.me/{SUPPORT_USERNAME}")

            text_reject = (
                "⚠️ <b>رسید پرداخت شما تأیید نشد!</b>\n\n"
                "تراکنش شما توسط ادمین رد شد. لطفاً جهت پیگیری به پشتیبانی پیام دهید:"
            )

            await callback.bot.send_message(
                chat_id=user_id,
                text=text_reject,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )

            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.reply(
                f"❌ <b>فیش شماره {receipt_id} متعلق به کاربر <code>{user_id}</code> رد شد و کاربر به پشتیبانی هدایت گردید.</b>",
                parse_mode="HTML"
            )

        except Exception as e:
            await callback.message.reply(f"❌ خطا در ارسال به کاربر ({user_id}):\n<code>{e}</code>", parse_mode="HTML")

