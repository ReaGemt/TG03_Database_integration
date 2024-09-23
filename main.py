import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aiosqlite

from config import TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    name = State()
    age = State()
    grade = State()

async def init_db():
    async with aiosqlite.connect('school_data.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                grade TEXT NOT NULL
            )
        ''')
        await db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_students_user_id ON students(user_id)')
        await db.commit()

@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.answer("Привет! Как тебя зовут?", reply_markup=ReplyKeyboardRemove())
    await Form.name.set()

@dp.message_handler(state=Form.name)
async def name(message: Message, state: FSMContext):
    if message.text.lower() == 'отменить':
        await cancel_handler(message, state)
        return
    await state.update_data(name=message.text)
    # Создаем клавиатуру с кнопкой "Отменить"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Отменить'))
    await message.answer("Сколько тебе лет?", reply_markup=keyboard)
    await Form.next()

@dp.message_handler(state=Form.age)
async def age(message: Message, state: FSMContext):
    if message.text.lower() == 'отменить':
        await cancel_handler(message, state)
        return
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректный возраст (число).")
        return
    age_value = int(message.text)
    if not (5 <= age_value <= 100):
        await message.answer("Пожалуйста, введите реальный возраст от 5 до 100.")
        return
    await state.update_data(age=age_value)
    grades = [str(i) for i in range(1, 12)]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    keyboard.add(*[KeyboardButton(grade) for grade in grades])
    keyboard.add(KeyboardButton('Отменить'))
    await message.answer("В каком ты классе?", reply_markup=keyboard)
    await Form.next()

@dp.message_handler(state=Form.grade)
async def grade(message: Message, state: FSMContext):
    if message.text.lower() == 'отменить':
        await cancel_handler(message, state)
        return
    await state.update_data(grade=message.text)
    data = await state.get_data()
    # Создаем инлайн-клавиатуру для подтверждения
    inline_keyboard = InlineKeyboardMarkup()
    inline_keyboard.add(InlineKeyboardButton('Подтвердить', callback_data='confirm'))
    inline_keyboard.add(InlineKeyboardButton('Отменить', callback_data='cancel'))
    await message.answer(
        f"Проверьте введенные данные:\n"
        f"Имя: {data['name']}\n"
        f"Возраст: {data['age']}\n"
        f"Класс: {data['grade']}",
        reply_markup=inline_keyboard
    )

@dp.callback_query_handler(Text(equals='confirm'), state=Form.grade)
async def process_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    try:
        async with aiosqlite.connect('school_data.db') as db:
            await db.execute('''
                INSERT OR REPLACE INTO students (user_id, name, age, grade) VALUES (?, ?, ?, ?)''',
                (callback_query.from_user.id, data['name'], data['age'], data['grade']))
            await db.commit()
        await bot.send_message(callback_query.from_user.id, "Данные сохранены.", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logging.error(f"Ошибка базы данных: {e}")
        await bot.send_message(callback_query.from_user.id, "Произошла ошибка при сохранении данных.")
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.finish()
    await callback_query.answer()

@dp.callback_query_handler(Text(equals='cancel'), state=Form.grade)
async def process_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.from_user.id, "Ввод данных отменен.", reply_markup=ReplyKeyboardRemove())
    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, reply_markup=None)
    await state.finish()
    await callback_query.answer()

@dp.message_handler(commands=['cancel'], state='*')
async def cancel_handler(message: Message, state: FSMContext):
    await state.finish()
    await message.answer("Ввод данных отменен.", reply_markup=ReplyKeyboardRemove())

@dp.message_handler(commands=['profile'])
async def profile(message: Message):
    async with aiosqlite.connect('school_data.db') as db:
        async with db.execute('SELECT name, age, grade FROM students WHERE user_id = ?', (message.from_user.id,)) as cursor:
            data = await cursor.fetchone()
            if data:
                name, age, grade = data
                await message.answer(f"Ваши данные:\nИмя: {name}\nВозраст: {age}\nКласс: {grade}")
            else:
                await message.answer("Вы еще не предоставили свои данные. Введите /start для начала.")

@dp.message_handler(commands=['update'])
async def update_data(message: Message):
    await message.answer("Давайте обновим ваши данные. Как вас зовут?", reply_markup=ReplyKeyboardRemove())
    await Form.name.set()

@dp.message_handler(commands=['delete'])
async def delete_data(message: Message):
    async with aiosqlite.connect('school_data.db') as db:
        await db.execute('DELETE FROM students WHERE user_id = ?', (message.from_user.id,))
        await db.commit()
    await message.answer("Ваши данные были удалены.")

@dp.message_handler(commands=['help'])
async def help_command(message: Message):
    await message.answer(
        "Я собираю информацию о студентах.\n"
        "Команды:\n"
        "/start - начать ввод данных\n"
        "/profile - посмотреть ваши данные\n"
        "/update - обновить ваши данные\n"
        "/delete - удалить ваши данные\n"
        "/help - показать эту справку"
    )

@dp.message_handler()
async def unknown_message(message: Message):
    await message.answer("Извините, я не понимаю это сообщение. Введите /help для списка доступных команд.")

async def on_startup(dp):
    await init_db()

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup)
