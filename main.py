import logging
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage  # Хранилище состояний в оперативной памяти
from aiogram.dispatcher import FSMContext  # Контекст для хранения состояний пользователя
from aiogram.dispatcher.filters import Text  # Фильтр для обработки текстовых сообщений и коллбэков
from aiogram.dispatcher.filters.state import State, StatesGroup  # Классы для создания машины состояний
from aiogram.types import (
    Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton  # Типы данных для работы с сообщениями и клавиатурами
)

from config import TOKEN  # Импортируем токен бота из файла конфигурации

# Настраиваем логирование для вывода информации в консоль
logging.basicConfig(level=logging.INFO)

# Инициализируем бота с заданным токеном
bot = Bot(token=TOKEN)
# Создаем хранилище состояний (используется для хранения данных между шагами диалога)
storage = MemoryStorage()
# Создаем диспетчер для обработки входящих сообщений и команд
dp = Dispatcher(bot, storage=storage)

# Определяем машину состояний для диалога с пользователем
class Form(StatesGroup):
    name = State()   # Состояние ожидания ввода имени
    age = State()    # Состояние ожидания ввода возраста
    grade = State()  # Состояние ожидания ввода класса

# Функция для инициализации базы данных
async def init_db():
    # Подключаемся к базе данных или создаем новую, если её нет
    async with aiosqlite.connect('school_data.db') as db:
        # Создаем таблицу студентов, если она ещё не существует
        await db.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                grade TEXT NOT NULL
            )
        ''')
        # Создаем уникальный индекс по полю user_id для предотвращения дублирования
        await db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_students_user_id ON students(user_id)')
        # Сохраняем изменения в базе данных
        await db.commit()

# Хендлер для команды /start — начало диалога
@dp.message_handler(commands=['start'])
async def start(message: Message):
    # Отправляем приветственное сообщение и удаляем предыдущие клавиатуры
    await message.answer("Привет! Как тебя зовут?", reply_markup=ReplyKeyboardRemove())
    # Устанавливаем состояние ожидания ввода имени
    await Form.name.set()

# Хендлер для получения имени от пользователя
@dp.message_handler(state=Form.name)
async def name(message: Message, state: FSMContext):
    # Проверяем, не хочет ли пользователь отменить ввод
    if message.text.lower() == 'отменить':
        await cancel_handler(message, state)
        return
    # Сохраняем имя пользователя в состоянии
    await state.update_data(name=message.text)
    # Создаем клавиатуру с кнопкой "Отменить"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Отменить'))
    # Запрашиваем возраст пользователя
    await message.answer("Сколько тебе лет?", reply_markup=keyboard)
    # Переходим к следующему состоянию — ожидание возраста
    await Form.next()

# Хендлер для получения возраста от пользователя
@dp.message_handler(state=Form.age)
async def age(message: Message, state: FSMContext):
    # Проверяем, не хочет ли пользователь отменить ввод
    if message.text.lower() == 'отменить':
        await cancel_handler(message, state)
        return
    # Проверяем, является ли введенный текст числом
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректный возраст (число).")
        return
    age_value = int(message.text)
    # Проверяем, что возраст находится в допустимых пределах
    if not (5 <= age_value <= 100):
        await message.answer("Пожалуйста, введите реальный возраст от 5 до 100.")
        return
    # Сохраняем возраст пользователя в состоянии
    await state.update_data(age=age_value)
    # Создаем список кнопок для выбора класса (с 1 по 11)
    grades = [str(i) for i in range(1, 12)]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    keyboard.add(*[KeyboardButton(grade) for grade in grades])
    keyboard.add(KeyboardButton('Отменить'))
    # Запрашиваем класс пользователя
    await message.answer("В каком ты классе\группе?", reply_markup=keyboard)
    # Переходим к следующему состоянию — ожидание класса
    await Form.next()

# Хендлер для получения класса от пользователя
@dp.message_handler(state=Form.grade)
async def grade(message: Message, state: FSMContext):
    # Проверяем, не хочет ли пользователь отменить ввод
    if message.text.lower() == 'отменить':
        await cancel_handler(message, state)
        return
    # Сохраняем класс пользователя в состоянии
    await state.update_data(grade=message.text)
    # Получаем все данные из состояния
    data = await state.get_data()
    # Создаем инлайн-клавиатуру для подтверждения или отмены введенных данных
    inline_keyboard = InlineKeyboardMarkup()
    inline_keyboard.add(InlineKeyboardButton('Подтвердить', callback_data='confirm'))
    inline_keyboard.add(InlineKeyboardButton('Отменить', callback_data='cancel'))
    # Отправляем пользователю собранные данные для проверки и подтверждения
    await message.answer(
        f"Проверьте введенные данные:\n"
        f"Имя: {data['name']}\n"
        f"Возраст: {data['age']}\n"
        f"Класс\группа: {data['grade']}",
        reply_markup=inline_keyboard
    )

# Хендлер для обработки подтверждения данных (нажатие на кнопку "Подтвердить")
@dp.callback_query_handler(Text(equals='confirm'), state=Form.grade)
async def process_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    try:
        # Подключаемся к базе данных и сохраняем данные пользователя
        async with aiosqlite.connect('school_data.db') as db:
            await db.execute('''
                INSERT OR REPLACE INTO students (user_id, name, age, grade) VALUES (?, ?, ?, ?)
            ''', (callback_query.from_user.id, data['name'], data['age'], data['grade']))
            await db.commit()
        # Отправляем сообщение об успешном сохранении данных
        await bot.send_message(callback_query.from_user.id, "Данные сохранены.", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        # Логируем ошибку и уведомляем пользователя
        logging.error(f"Ошибка базы данных: {e}")
        await bot.send_message(callback_query.from_user.id, "Произошла ошибка при сохранении данных.")
    # Удаляем инлайн-клавиатуру из сообщения
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    # Завершаем состояние
    await state.finish()
    # Отвечаем на коллбэк, чтобы убрать иконку загрузки
    await callback_query.answer()

# Хендлер для обработки отмены ввода данных (нажатие на кнопку "Отменить")
@dp.callback_query_handler(Text(equals='cancel'), state=Form.grade)
async def process_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    # Отправляем сообщение об отмене ввода данных
    await bot.send_message(callback_query.from_user.id, "Ввод данных отменен.", reply_markup=ReplyKeyboardRemove())
    # Удаляем инлайн-клавиатуру из сообщения
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    # Завершаем состояние
    await state.finish()
    # Отвечаем на коллбэк
    await callback_query.answer()

# Хендлер для команды /cancel — позволяет пользователю отменить текущий ввод
@dp.message_handler(commands=['cancel'], state='*')
async def cancel_handler(message: Message, state: FSMContext):
    # Завершаем текущее состояние
    await state.finish()
    # Отправляем сообщение об отмене и удаляем клавиатуру
    await message.answer("Ввод данных отменен.", reply_markup=ReplyKeyboardRemove())

# Хендлер для команды /profile — отображает сохраненные данные пользователя
@dp.message_handler(commands=['profile'])
async def profile(message: Message):
    # Подключаемся к базе данных и извлекаем данные пользователя по его user_id
    async with aiosqlite.connect('school_data.db') as db:
        async with db.execute(
            'SELECT name, age, grade FROM students WHERE user_id = ?',
            (message.from_user.id,)
        ) as cursor:
            data = await cursor.fetchone()
            if data:
                name, age, grade = data
                # Отправляем пользователю его данные
                await message.answer(f"Ваши данные:\nИмя: {name}\nВозраст: {age}\nКласс: {grade}")
            else:
                # Если данных нет, предлагаем начать ввод
                await message.answer("Вы еще не предоставили свои данные. Введите /start для начала.")

# Хендлер для команды /update — позволяет обновить данные пользователя
@dp.message_handler(commands=['update'])
async def update_data(message: Message):
    # Начинаем процесс сбора данных заново
    await message.answer("Давайте обновим ваши данные. Как вас зовут?", reply_markup=ReplyKeyboardRemove())
    # Устанавливаем состояние ожидания ввода имени
    await Form.name.set()

# Хендлер для команды /delete — удаляет данные пользователя из базы
@dp.message_handler(commands=['delete'])
async def delete_data(message: Message):
    # Подключаемся к базе данных и удаляем запись пользователя
    async with aiosqlite.connect('school_data.db') as db:
        await db.execute('DELETE FROM students WHERE user_id = ?', (message.from_user.id,))
        await db.commit()
    # Отправляем сообщение об успешном удалении данных
    await message.answer("Ваши данные были удалены.")

# Хендлер для команды /help — выводит справку по командам
@dp.message_handler(commands=['help'])
async def help_command(message: Message):
    # Отправляем список доступных команд и их описание
    await message.answer(
        "Я собираю информацию о студентах.\n"
        "Команды:\n"
        "/start - начать ввод данных\n"
        "/profile - посмотреть ваши данные\n"
        "/update - обновить ваши данные\n"
        "/delete - удалить ваши данные\n"
        "/help - показать эту справку"
    )

# Хендлер для обработки неизвестных сообщений
@dp.message_handler()
async def unknown_message(message: Message):
    # Уведомляем пользователя, что команда не распознана
    await message.answer("Извините, я не понимаю это сообщение. Введите /help для списка доступных команд.")

# Функция, выполняемая при запуске бота
async def on_startup(dp):
    # Инициализируем базу данных
    await init_db()

# Точка входа в программу
if __name__ == '__main__':
    from aiogram import executor
    # Запускаем поллинг для обработки обновлений
    executor.start_polling(dp, on_startup=on_startup)
