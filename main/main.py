from aiogram.client.session.aiohttp import AiohttpSession
import asyncio
import re
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from aiogram.types import ReplyKeyboardRemove
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
import logging
from states import AddWorker, UpdateWorker, ReportState
from buttons import get_filial_kb, get_phone_kb, get_status_kb
from database import add_worker_to_db, update_worker_time, get_worker_by_id, get_all_workers, delete_worker_from_db
from securitiy import ADMINS, GROUP_ID
from aiogram import types, F
logging.basicConfig(level=logging.INFO)
tashkent_tz = pytz.timezone('Asia/Tashkent')
hozir = datetime.now(tashkent_tz)
target_time = (datetime.now() + timedelta(minutes=10)).strftime("%H:%M")
dp = Dispatcher()
bot = Bot(token="8607811325:AAF9QItvZIhxv3x4edRba-wS8wbUwSYVp2Y")

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) > 1 and args[1] == "check":
        worker = get_worker_by_id(user_id)
        if worker:
            await message.answer(
                f"Assalomu alaykum, {worker[1]}!\nIltimos, hozirgi holatingizni tanlang:",
                reply_markup=get_status_kb()
            )
        else:
            await message.answer("Siz bazada yo'qsiz. Managerga murojaat qiling.")
        return

    if user_id in ADMINS:
        await message.answer("👋 **Assalomu alaykum, Admin!**\n\n"
            "Bot boshqaruv paneli ishga tushdi. Quyidagi buyruqlardan foydalanishingiz mumkin:\n\n"
            "➕ /add_worker — Yangi ishchi qo'shish\n"
            "📊 /workers_info — Ishchilar ma'lumotlarini ko'rish\n"
            "⚙️ /workers — Ishchilar ma'lumotlarini tahrirlash\n\n"
            "Kerakli bo'limni tanlang:")
    else:
        await message.answer("Botga xush kelibsiz! Hisobot topshirish uchun guruhdagi tugmani bosing.")


@dp.message(Command("add_worker"))
async def start_add(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Sizda bunday huquq yo'q!")
        return

    await message.answer("1. Ishchining Telegram ID raqamini yozing:")
    await state.set_state(AddWorker.user_id)


@dp.message(AddWorker.user_id)
async def get_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Faqat raqam yozing:")
        return
    await state.update_data(u_id=message.text)
    await message.answer("2. Ishchining Ism va Familiyasini yozing:")
    await state.set_state(AddWorker.name)


@dp.message(AddWorker.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("3. Telefon raqamini yozing yoki tugmani bosing:", reply_markup=get_phone_kb())
    await state.set_state(AddWorker.phone)


@dp.message(AddWorker.phone)
async def get_phone(message: types.Message, state: FSMContext):
    # Agar foydalanuvchi tugmani bossa message.contact keladi, aks holda message.text
    p_num = message.contact.phone_number if message.contact else message.text

    # Kichik tekshiruv: foydalanuvchi buyruq yuborib yubormadimi?
    if p_num.startswith('/'):
        await message.answer("⚠️ Iltimos, avval telefon raqamini kiriting yoki tugmani bosing:")
        return

    await state.update_data(phone=p_num)
    await message.answer("4. Qaysi filialda ishlaydi?", reply_markup=get_filial_kb())
    await state.set_state(AddWorker.filial)

@dp.message(AddWorker.filial)
async def get_filial(message: types.Message, state: FSMContext):
    await state.update_data(filial=message.text)
    await message.answer("5. Ish boshlash vaqtini yozing (masalan, 08:00):")
    await state.set_state(AddWorker.work_time)


@dp.message(AddWorker.work_time)
async def get_time(message: types.Message, state: FSMContext):
    if not re.match(r"^\d{2}:\d{2}$", message.text):
        await message.answer("⚠️ Vaqtni 00:00 formatida yozing:")
        return

    data = await state.get_data()

    add_worker_to_db(
        data['u_id'],
        data['name'],
        data['phone'],
        data['filial'],
        message.text
    )

    await message.answer(f"✅ Ishchi muvaffaqiyatli qo'shildi!", reply_markup=ReplyKeyboardRemove())
    await state.clear()


@dp.message(Command("workers_info"))
async def show_workers(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Bu ma'lumotlar faqat adminlar uchun!")
        return

    workers = get_all_workers()

    if not workers:
        await message.answer("📭 Hozircha ishchilar qo'shilmagan.")
        return

    text = "📋 **Ishchilar ro'yxati:**\n\n"

    for w in workers:
        worker_info = (
            f"👤 **Ism:** {w[1]}\n"
            f"🆔 **ID:** `{w[0]}`\n"
            f"📞 **Tel:** {w[2]}\n"
            f"📍 **Filial:** {w[3]}\n"
            f"⏰ **Ish vaqti:** {w[4]}\n"
            f"{'—' * 15}\n"
        )
        text += worker_info

    await message.answer(text, parse_mode="Markdown")


@dp.message(Command("get_group_id"))
async def get_id(message: types.Message):
    chat_id = message.chat.id
    await message.answer(f"Bu guruhning ID-si: `{chat_id}`", parse_mode="Markdown")


@dp.message(F.text == "/workers")
async def show_workers(message: types.Message):
    workers = get_all_workers()
    if not workers:
        await message.answer("Bazada hech qanday ishchi yo'q.")
        return

    for w in workers:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_{w[0]}")],
            [types.InlineKeyboardButton(text="O'zartirish", callback_data=f"edit_{w[0]}")]
        ])

        text = (f"👤 **Ism:** {w[1]}\n"
                f"📞 **Tel:** {w[2]}\n"
                f"⏰ **Ish vaqti:** {w[4]}")

        await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@dp.callback_query(F.data.startswith("del_"))
async def callbacks_num(callback: types.CallbackQuery):
    user_id = callback.data.split("_")[1]
    delete_worker_from_db(user_id)
    await callback.message.edit_text("✅ Ishchi bazadan o'chirildi!")
    await callback.answer()


@dp.callback_query(F.data.startswith("edit_"))
async def edit_worker_start(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.data.split("_")[1]
    await state.update_data(edit_user_id=user_id)
    await callback.message.answer("Yangi ish vaqtini kiriting (masalan, 09:00):")
    await state.set_state(UpdateWorker.waiting_for_new_time)
    await callback.answer()


@dp.message(UpdateWorker.waiting_for_new_time)
async def update_time_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("edit_user_id")
    new_time = message.text

    update_worker_time(user_id, new_time)

    await message.answer(f"✅ Vaqt muvaffaqiyatli {new_time} ga o'zgartirildi!")
    await state.clear()


# time management

@dp.message(Command("test_group"))
async def test_group_message(message: types.Message):
    print(f"Test buyrug'i keldi! Guruhga yuborishga harakat qilyapman: {GROUP_ID}")
    try:
        await bot.send_message(chat_id=GROUP_ID, text="🤖 Salom! Guruh bilan aloqa o'rnatildi!")
        await message.answer("✅ Guruhga xabar yuborildi!")
    except Exception as e:
        print(f"❌ XATO: {e}")
        await message.answer(f"❌ Guruhga yuborib bo'lmadi. Xato: {e}")


async def send_report_to_admins(user_id, status_text):
    worker = get_worker_by_id(user_id)
    if worker:
        report = (f"📢 **YANGI HISOBOT**\n\n"
                  f"👤 Ishchi: {worker[1]}\n"
                  f"📞 Tel: {worker[2]}\n"
                  f"📍 Holati: {status_text}")

        for admin_id in ADMINS:
            try:
                await bot.send_message(chat_id=admin_id, text=report, parse_mode="Markdown")
            except Exception as e:
                print(f"Admin {admin_id} ga xabar ketmadi: {e}")


async def send_report_to_group(user_id, status_text):
    worker = get_worker_by_id(user_id)

    if worker:
        report = (f"📢 **YANGI HISOBOT**\n\n"
                  f"👤 Ishchi: {worker[1]}\n"
                  f"📞 Tel: {worker[2]}\n"
                  f"📍 Holati: {status_text}")

        try:
            # Siklsiz, to'g'ridan-to'g'ri GROUP_ID ga yuboramiz
            await bot.send_message(
                chat_id=GROUP_ID,
                text=report,
                parse_mode="Markdown"
            )
            print(f"✅ Guruhga hisobot yuborildi.")
        except Exception as e:
            print(f"❌ Guruhga xabar yuborishda xato: {e}")


async def auto_reminder():
    hozir = datetime.now(tashkent_tz)
    target_time = (hozir + timedelta(minutes=15)).strftime("%H:%M")

    print(f"--- Tekshiruv: {hozir.strftime('%H:%M')} | Qidirilmoqda: {target_time} ---")

    workers = get_all_workers()

    for w in workers:
        baza_vaqti = str(w[4]).strip()

        if baza_vaqti == target_time:
            ism_familiya = w[1]
            inline_kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="Javob berish ✍️",
                    url="https://t.me/caffeine_manager_bot?start=check"
                )]
            ])

            try:
                await bot.send_message(
                    chat_id=GROUP_ID,
                    text=f"🔔 {ism_familiya} ishga kelyapsizmi?",
                    reply_markup=inline_kb
                )
                print(f"✅ Guruhga yuborildi: {ism_familiya}")
            except Exception as e:
                print(f"❌ Xato: {e}")


@dp.callback_query(F.data.startswith("status_"))
async def handle_status(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    if callback.data == "status_late":
        await callback.message.edit_text("⚠️ Iltimos, kech qolishingiz sababini qisqacha yozib yuboring:")
        await state.set_state(ReportState.waiting_for_reason)
    else:
        status_text = "✅ Ishxonada" if callback.data == "status_at_work" else "🏃 Yo'lda (vaqtida)"
        await send_report_to_group(user_id, status_text)
        await callback.message.edit_text(f"Rahmat! Holatingiz: {status_text} deb belgilandi.")

    await callback.answer()


@dp.message(ReportState.waiting_for_reason)
async def process_late_reason(message: types.Message, state: FSMContext):
    reason = message.text
    user_id = message.from_user.id

    status_with_reason = f"⏰ Kech qoladi\n📝 Sababi: {reason}"

    await send_report_to_group(user_id, status_with_reason)

    await message.answer("✅ Rahmat! Sabab adminlarga yetkazildi.")
    await state.clear()


import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler


# ... boshqa importlar va dp, bot obyekti ...

async def main():
    # 1. Shlyuzni (Scheduler) sozlash
    scheduler = AsyncIOScheduler(timezone='Asia/Tashkent')

    # Ishni qo'shish
    scheduler.add_job(auto_reminder, "interval", minutes=1)

    # Schedulerni ishga tushirish
    scheduler.start()

    try:
        # 2. Botni polling rejimida ishga tushirish
        # skip_updates=True qilsangiz, bot o'chiq bo'lgan vaqtdagi xabarlarni e'tiborsiz qoldiradi
        await dp.start_polling(bot, skip_updates=True)
    finally:
        # Bot to'xtaganda sessiyani yopish (xatolik bermasligi uchun)
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # Konsolda Ctrl+C bosilganda chiroyli to'xtashi uchun
        print("Bot to'xtatildi")
