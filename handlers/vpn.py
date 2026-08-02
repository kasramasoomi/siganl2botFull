import time, json, uuid, aiohttp, sqlite3, logging
from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import API_TOKEN, INBOUND_TEST, SUPPORT_ID, check_and_update_admin
from handlers.common import check_subscription, send_join_prompt

router = Router()

async def create_xui_config(inbound_id, user_name, gb_limit, days=30):
    target_port = 22907 if int(inbound_id) == INBOUND_TEST else 17589
    urls_to_try = ["https://127.0.0.1:5379/YY6y6LwMYl9NxSt20H", "https://siganl.xyz:5379/YY6y6LwMYl9NxSt20H"]
    connector = aiohttp.TCPConnector(ssl=False)
    client_uuid = str(uuid.uuid4())
    expiry_time = int((time.time() + (days * 86400)) * 1000) if days else 0
    email = user_name.replace(" ", "_")
    total_bytes = int(gb_limit) * 1024 * 1024 * 1024
    
    payload_new = {
        "client": {"id": client_uuid, "email": email, "totalGB": total_bytes, "expiryTime": expiry_time, "enable": True, "flow": "", "limitIp": 0, "tgId": 0, "subId": ""},
        "inboundIds": [int(inbound_id)]
    }
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Authorization": f"Bearer {API_TOKEN.strip()}"}

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        for current_base in urls_to_try:
            try:
                async with session.post(f"{current_base.strip().rstrip('/')}/panel/api/clients/add", json=payload_new, timeout=10) as resp:
                    if resp.status == 200:
                        return f"vless://{client_uuid}@siganl.xyz:{target_port}?encryption=none&security=none&type=tcp#User_{email}", None
            except Exception:
                pass
        return None, "خطا در اتصال به پنل X-UI"

@router.message(F.text == "🔑 خدمات VPN", StateFilter("*"))
async def vpn_menu(message: types.Message, state: FSMContext):
    await state.clear()
    check_and_update_admin(message.from_user)
    if not await check_subscription(message.from_user.id): return await send_join_prompt(message)
    kb = InlineKeyboardBuilder()
    kb.button(text="🎁 دریافت تست ۱ روزه (1GB)", callback_data="get_test")
    kb.button(text="🛒 خرید اشتراک", callback_data="buy_start")
    kb.adjust(1)
    await message.answer("سرویس مورد نظر را انتخاب کنید:", reply_markup=kb.as_markup())

@router.callback_query(F.data == "get_test")
async def get_test(callback: types.CallbackQuery):
    check_and_update_admin(callback.from_user)
    if not await check_subscription(callback.from_user.id): return await callback.answer("⚠️ ابتدا عضو کانال شوید.", show_alert=True)
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM testers WHERE user_id = ?", (callback.from_user.id,))
    if cursor.fetchone():
        await callback.message.answer("❌ شما قبلاً تست رایگان گرفته‌اید!")
    else:
        status_msg = await callback.message.answer("⏳ در حال ساخت کانفیگ...")
        config, err_msg = await create_xui_config(INBOUND_TEST, callback.from_user.full_name or f"User_{callback.from_user.id}", 1, days=1)
        await status_msg.delete()
        if config:
            cursor.execute("INSERT INTO testers (user_id) VALUES (?)", (callback.from_user.id,))
            conn.commit()
            await callback.message.answer(f"✅ کانفیگ تست:\n\n`{config}`", parse_mode="Markdown")
        else:
            await callback.message.answer(f"❌ خطا: {err_msg}")
    conn.close()
    await callback.answer()
