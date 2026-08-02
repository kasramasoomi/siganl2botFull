from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from database import main_menu

router = Router()

async def check_subscription(user_id):
    # تابع چک عضویت کانال (تطبیق با کدهای قبلی پروژه)
    return True

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    # پاک کردن کاملاً تمام استیت‌ها و مراحل قبلی (مثل مرحله خرید)
    await state.clear()
    
    await message.answer(
        f"سلام {message.from_user.first_name} عزیز! 👋\nبه ربات خوش آمدید. لطفاً گزینه مورد نظر را انتخاب کنید:",
        reply_markup=main_menu()
    )
