from aiogram.fsm.state import StatesGroup, State


class AddWorker(StatesGroup):
    user_id = State()  # Telegram ID uchun
    name = State()  # Ism-familiya
    phone = State()  # Telefon
    filial = State()  # Filial
    work_time = State()  # Ish vaqti (08:00)

class UpdateWorker(StatesGroup):
    waiting_for_new_time = State()

class Form(StatesGroup):
    waiting_reason = State()


from aiogram.fsm.state import State, StatesGroup

class ReportState(StatesGroup):
    waiting_for_reason = State()