from aiogram.client.session.aiohttp import AiohttpSession
import asyncio
import re
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from database import init_db
from aiogram.types import ReplyKeyboardRemove
import pytz
import sqlite3
import logging
from states import AddWorker, UpdateWorker, ReportState
from buttons import get_filial_kb, get_phone_kb, get_status_kb
from database import add_worker_to_db, update_worker_time, get_worker_by_id, get_all_workers, delete_worker_from_db
from securitiy import ADMINS
from aiogram import types, F





logging.basicConfig(level=logging.INFO)

tashkent_tz = pytz.timezone('Asia/Tashkent')

# Hozirgi vaqtni Toshkent vaqti bilan olish
hozir = datetime.now(tashkent_tz)

# Target vaqtni ham Toshkent vaqtiga nisbatan 10 daqiqa qo'shib olish
# datetime.now() ichiga tashkent_tz berilishi shart
target_time = (datetime.now(tashkent_tz) + timedelta(minutes=10)).strftime("%H:%M")

dp = Dispatcher()
bot = Bot(token="8607811325:AAF9QItvZIhxv3x4edRba-wS8wbUwSYVp2Y")
GROUP_ID = -1002593004859
WORK_PHONE_ID = 6531070045
WORK_PHONE_ID_2 = 8159413536


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    # message.text dan keyingi parametrlarni olish (Deep Linking)
    args = message.text.split()

    # Agar link orqali (t.me/bot?start=...) kelgan bo'lsa
    if len(args) > 1:
        param = args[1]  # Masalan: "check_1234567"

        if param.startswith("check_"):
            try:
                # ID ni ajratib olamiz
                target_worker_id = int(param.replace("check_", ""))

                # 1. Xavfsizlik tekshiruvi: Tugmani bosgan odam ID si linkdagi ID ga tengmi?
                if user_id != target_worker_id:
                    await message.answer(
                        "⚠️ Kechirasiz, siz boshqa ishchining tugmasini bosdingiz. \n"
                        "Faqat o'zingiz uchun hisobot bera olasiz!"
                    )
                    return

                # 2. Bazadan ishchini qidiramiz
                worker = get_worker_by_id(user_id)
                if worker:
                    await message.answer(
                        f"Assalomu alaykum, {worker[1]}!\n"
                        f"Iltimos, hozirgi holatingizni tanlang:",
                        reply_markup=get_status_kb()
                    )
                else:
                    await message.answer("❌ Siz bazada topilmadingiz. Managerga murojaat qiling.")

                return  # Deep link ishini bitirdi, pastga tushmaydi

            except ValueError:
                await message.answer("⚠️ Noto'g'ri parametr yuborildi.")
                return

    # Agar oddiy /start bosilgan bo'lsa yoki Deep Link xato bo'lsa
    if user_id in ADMINS:
        await message.answer("👋 **Assalomu alaykum, Admin!**\n\n"
                             "Bot boshqaruv paneli ishga tushdi. /add_worker orqali ishchi qo'shishingiz mumkin.")
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
    p_num = message.contact.phone_number if message.contact else message.text

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


async def send_report_to_group(user_id: int, status_text: str):
    conn = sqlite3.connect('cafe_work.db')
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT full_name, phone, filial FROM workers WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
    except Exception as e:
        print(f"Bazadan ma'lumot olishda xato: {e}")
        user_data = None
    finally:
        conn.close()

    if user_data:
        full_name, phone, filial = user_data
        current_time = datetime.now(tashkent_tz).strftime("%H:%M")

        report_message = (
            f"📊 **YANGI HISOBOT**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 **Ishchi:** {full_name}\n"
            f"📍 **Filial:** {filial}\n"
            f"📞 **Tel:** {phone}\n"
            f"🕒 **Vaqt:** {current_time}\n"
            f"📝 **Holati:** {status_text}\n"
            f"━━━━━━━━━━━━━━━"
        )


        try:
            await bot.send_message(chat_id=GROUP_ID, text=report_message, parse_mode="Markdown")
        except Exception as e:
            print(f"Guruhga xabar yuborishda xato: {e}")
    else:
        print(f"Xato: {user_id} ID li ishchi 'workers' jadvalidan topilmadi!")


@dp.callback_query(F.data.startswith("status_"))
async def handle_status(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    worker = get_worker_by_id(user_id)  # Bazadan ma'lumotni olamiz

    if not worker:
        await callback.answer("Xatolik: Siz bazada yo'qsiz!", show_alert=True)
        return

    full_name = worker[1]
    filial_nomi = worker[3]  # "Riviera" yoki boshqasi

    # 1. AGAR KECH QOLSA (Sababini so'raymiz)
    if callback.data == "status_late":
        await callback.message.edit_text("⚠️ Iltimos, kech qolishingiz sababini qisqacha yozib yuboring:")
        await state.set_state(ReportState.waiting_for_reason)

    # 2. AGAR DAM OLISH BO'LSA
    elif callback.data == "status_day_off":
        await callback.message.edit_text(f"✅ Dam olish kuni belgilandi. ({filial_nomi})")
        await send_report_to_group(user_id, f"🏖 Bugun dam olish kuni")

    # 3. AGAR ISHXONADA YOKI YO'LDA BO'LSA (Tasdiqlashga yuboramiz)
    elif callback.data in ["status_at_work", "status_on_way"]:
        status_label = "Ishxonada" if callback.data == "status_at_work" else "Yo'lda (vaqtida)"

        await callback.message.edit_text(
            f"⏳ {status_label} holati tanlandi. Tasdiqlash uchun '{filial_nomi}' Receptionga xabar yuborildi.")

        builder = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Ha, keldi", callback_data=f"confirm_arrival_{user_id}_{callback.data}")]
        ])


        target_chat = WORK_PHONE_ID_2 if filial_nomi == "Riviera" else WORK_PHONE_ID

        await bot.send_message(
            chat_id=target_chat,
            text=(f"🔔 **TASDIQLASH SO'ROVI**\n\n"
                  f"👤 Ishchi: **{full_name}**\n"
                  f"🏢 Filial: **{filial_nomi}**\n"
                  f"📍 Holati: **{status_label}**\n\n"
                  f"Ushbu ishchi kelganini tasdiqlaysizmi?"),
            reply_markup=builder,
            parse_mode="Markdown"
        )

    await callback.answer()


@dp.callback_query(F.data.startswith("confirm_arrival_"))
async def confirm_by_office_phone(callback: types.CallbackQuery):
    data = callback.data.split("_")
    user_id = int(data[2])  # ID ni son ko'rinishida olamiz
    status_key = "_".join(data[3:])  # status_at_work yoki status_on_way

    worker = get_worker_by_id(user_id)

    if not worker:
        await callback.answer("Xatolik: Ishchi topilmadi!")
        return

    full_name = worker[1]
    filial_nomi = worker[3]
    current_time = datetime.now(tashkent_tz).strftime("%H:%M")

    status_text = "✅ Ishxonada" if status_key == "status_at_work" else "🏃 Keldi (yo'ldan)"


    report_text = f"{status_text} (Filial: {filial_nomi})"
    await send_report_to_group(user_id, report_text)

    await callback.message.edit_text(
        f"👌 **{full_name}** tasdiqlandi.\n"
        f"🏢 Filial: {filial_nomi}\n"
        f"⏰ Vaqt: {current_time}\n"
        f"✅ Hisobot guruhga yuborildi."
    )

    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"✅ Kelganingiz **{filial_nomi}** reception tomonidan tasdiqlandi. Ishga marhamat!"
        )
    except Exception as e:
        print(f"Xabarni yuborishda xato: {e}")

    await callback.answer()


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





@dp.message(ReportState.waiting_for_reason)
async def process_late_reason(message: types.Message, state: FSMContext):
    reason = message.text
    user_id = message.from_user.id

    status_with_reason = f"⏰ Kech qolaman\n📝 Sababi: {reason}"

    await send_report_to_group(user_id, status_with_reason)

    await message.answer("✅ Rahmat! Sabab adminlarga yetkazildi.")
    await state.clear()


@dp.callback_query(F.data == "questions")
async def ask_for_question(callback: types.CallbackQuery, state: FSMContext):
    # Ishchiga savol beramiz
    await callback.message.edit_text(
        "📝 Savol yoki taklifingiz bo'lsa, pastga yozib yuboring. Adminlar ko'rib chiqishadi:")

    # Botni "Savol kutish" holatiga o'tkazamiz
    await state.set_state(ReportState.waiting_for_question)
    await callback.answer()


@dp.message(ReportState.waiting_for_question)
async def process_question(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_text = message.text  # Ishchi yozgan gap

    conn = sqlite3.connect('cafe_work.db')
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, filial FROM workers WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    full_name = user_data[0] if user_data else "Noma'lum ishchi"
    filial = user_data[1] if user_data else "Noma'lum filial"

    admin_notification = (
        f"📩 **YANGI MUROJAAT**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 **Ishchi:** {full_name}\n"
        f"📍 **Filial:** {filial}\n"
        f"🆔 **ID:** {user_id}\n\n"
        f"💬 **Xabar:** {user_text}\n"
        f"━━━━━━━━━━━━━━━"
    )

    # 3. Har bir adminga alohida xabar yuborish
    for admin_id in ADMINS:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_notification, parse_mode="Markdown")
        except Exception as e:
            print(f"Adminga ({admin_id}) xabar ketmadi: {e}")

    # 4. Ishchiga javob qaytarish va holatni tozalash
    await message.answer("✅ Rahmat! Sizning xabaringiz adminlarga shaxsiy xabar sifatida yetkazildi.")
    await state.clear()


import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def main():
    scheduler = AsyncIOScheduler(timezone='Asia/Tashkent')

    scheduler.add_job(auto_reminder, "interval", minutes=1)

    scheduler.start()

    try:
        # 2. Botni polling rejimida ishga tushirish
        # skip_updates=True qilsangiz, bot o'chiq bo'lgan vaqtdagi xabarlarni e'tiborsiz qoldiradi
        await dp.start_polling(bot, skip_updates=True)
    finally:
        # Bot to'xtaganda sessiyani yopish (xatolik bermasligi uchun)
        await bot.session.close()


init_db()
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi")
