import sqlite3
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import bot, ADMIN_IDS, PRICES, CARD_INFO, SUPPORT_ID, check_and_update_admin
from database import States, plan_menu
from handlers.common import check_subscription

router = Router()

@router.callback_query(F.data == "buy_start")
async def buy_start(callback: types.CallbackQuery):
    check_and_update_admin(callback.from_user)
    if not await check_subscription(callback.from_user.id): return await callback.answer("⚠️ ابتدا عضو کانال شوید.", show_alert=True)
    await callback.message.answer("لطفاً حجم مورد نظر را انتخاب کنید:", reply_markup=plan_menu())
    await callback.answer()

@router.callback_query(F.data.startswith("buy_"))
async def select_plan(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "buy_start": return
    gb = callback.data.split("_")[1]
    await state.update_data(gb=gb)
    await state.set_state(States.waiting_for_name)
    await callback.message.answer(f"📦 بسته {gb} گیگابایت.\n\nلطفاً نام خود را وارد کنید:")
    await callback.answer()

@router.message(States.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    if message.text in ["/start", "/cancel"]:
        await state.clear()
        return await message.answer("❌ عملیات خرید لغو شد. مجدداً /start را بزنید.")
    if not message.text: return await message.answer("❌ لطفاً نام خود را متنی وارد کنید.")
    
    input_name = message.text.strip()
    await state.update_data(full_name=input_name)
    data = await state.get_data()
    gb = data.get("gb", "10")
    price = PRICES.get(gb, "100,000")
    await message.answer(
        f"📥 فاکتور خرید:\n👤 نام: {input_name}\n📦 حجم: {gb} گیگابایت\n💵 مبلغ: {price} تومان\n\n💳 شماره کارت:\n`{CARD_INFO}`\n\nلطفاً عکس رسید را بفرستید.",
        parse_mode="Markdown"
    )
    await state.set_state(States.waiting_for_receipt)

@router.message(States.waiting_for_receipt)
async def get_receipt(message: types.Message, state: FSMContext):
    # اگر کاربر استارت یا انصراف داد، از مرحله خرید خارج شود
    if message.text in ["/start", "/cancel"]:
        await state.clear()
        return await message.answer("❌ عملیات خرید لغو شد. مجدداً /start را بزنید.")

    if not message.photo: return await message.answer("❌ لطفاً عکس رسید ارسال کنید.")
    data = await state.get_data()
    gb, name = data.get("gb", "10"), data.get("full_name", "کاربر")
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO receipts (user_id, full_name, gb, photo_file_id) VALUES (?, ?, ?, ?)", (message.from_user.id, name, gb, message.photo[-1].file_id))
    receipt_id = cursor.lastrowid
    conn.commit()
    conn.close()

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ تایید", callback_data=f"app_{receipt_id}")
    kb.button(text="❌ رد", callback_data=f"rej_{receipt_id}")

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(admin_id, message.photo[-1].file_id, caption=f"🚨 رسید جدید!\n👤 {name}\n📦 {gb}GB\n🆔 {message.from_user.id}", reply_markup=kb.as_markup())
        except Exception as e: 
            print(f"Error sending photo to admin {admin_id}: {e}")
            
    await message.answer("✅ رسید ثبت شد و برای ادمین ارسال گردید.")
    await state.clear()
