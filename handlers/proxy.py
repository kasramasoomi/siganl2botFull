from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

DOMAIN = "proxy.siganl.xyz"
IP = "65.109.191.196"
SECRET = "ee41664db040500920a1d78d212d41223f63646e2e636c6f7564666c6172652e636f6d"

PROXY_1 = f"https://t.me/proxy?server={DOMAIN}&port=8443&secret={SECRET}"
PROXY_2 = f"https://t.me/proxy?server={IP}&port=8443&secret={SECRET}"

def get_proxy_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 سرور اول (دامنه اصلی - پورت 8443)", url=PROXY_1)
    kb.button(text="⚡ سرور دوم (آی‌پی مستقیم - پورت 8443)", url=PROXY_2)
    kb.adjust(1)
    return kb.as_markup()

@router.message(F.text == "🌐 پراکسی تلگرام")
@router.message(F.text.contains("پراکسی") | F.text.contains("proxy") | F.text.contains("Proxy"))
async def send_proxies(message: types.Message):
    await message.answer(
        "🌐 **لیست سرورهای پراکسی اختصاصی (پرسرعت و پایدار)**\n\nجهت اتصال، یکی از سرورهای زیر را انتخاب کنید:",
        reply_markup=get_proxy_keyboard(),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
