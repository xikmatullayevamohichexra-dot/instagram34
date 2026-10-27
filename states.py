from aiogram.fsm.state import State, StatesGroup


class BotStates(StatesGroup):
    ai_chat = State()      # AI suhbat rejimi holati
    book_search = State()  # Kitob qidirish rejimi holati

