import os
import logging
import random
import string
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv

# --- Загрузка переменных окружения ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Отсутствует токен бота в переменных окружения")

# --- Логирование ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename="bot.log",
    encoding="utf-8"
)
logger = logging.getLogger(__name__)

# --- Инициализация бота и диспетчера ---
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)

# --- База данных ---
conn = sqlite3.connect("tickets.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    code TEXT PRIMARY KEY,
    user_id INTEGER,
    problem TEXT,
    status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS problem_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT,
    count INTEGER DEFAULT 1
)
""")
conn.commit()

# --- Прощальные фразы ---
FAREWELL_PHRASES = [
    "Обращайтесь снова! 😊",
    "Спасибо, что выбрали LKN VPN!",
    "Желаем вам отличного дня! 🚀",
    "Всегда рады помочь!",
    "Будьте на связи! 📡",
    "VPN с любовью от LKN 💙",
    "Ваш комфорт — наша задача!",
    "Надеемся, всё решилось!",
    "Возвращайтесь, если что-то ещё понадобится.",
    "Мы рядом 24/7 для вас!",
    "Спасибо за использование нашего сервиса!",
    "Хорошего дня и безопасного интернета!",
]

# --- States ---
class Form(StatesGroup):
    waiting_for_device = State()
    waiting_for_server = State()
    waiting_for_country = State()
    waiting_for_resolve = State()
    waiting_for_problem_desc = State()
    waiting_for_idea = State()
    waiting_for_rating = State()
    waiting_for_manager_problem = State()

# --- Клавиатуры ---

def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Как подключить VPN", callback_data="how_connect"),
        InlineKeyboardButton("Не работает VPN", callback_data="vpn_not_work"),
        InlineKeyboardButton("Сбор ip, логов", callback_data="logs"),
        InlineKeyboardButton("Когда платная подписка", callback_data="paid_subscription"),
        InlineKeyboardButton("Предложить инновации", callback_data="ideas"),
        InlineKeyboardButton("Как работает РФ сервер", callback_data="rf_server"),
    )
    return kb

def device_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Android", callback_data="device_Android"),
        InlineKeyboardButton("MacOS", callback_data="device_MacOS"),
        InlineKeyboardButton("Windows", callback_data="device_Windows"),
        InlineKeyboardButton("IOS", callback_data="device_IOS"),
    )
    return kb

def server_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Россия 🇷🇺", callback_data="server_Russia"),
        InlineKeyboardButton("Нидерланды 🇳🇱", callback_data="server_Netherlands"),
    )
    return kb

def countries_menu():
    countries_list = ["Украина", "Россия", "США", "Великобритания", "Казахстан", "Беларусь", "Нет моей страны"]
    kb = InlineKeyboardMarkup(row_width=2)
    for country in countries_list:
        kb.insert(InlineKeyboardButton(country, callback_data=f"country_{country}"))
    return kb

def resolve_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Решено", callback_data="resolved"),
        InlineKeyboardButton("Не решено", callback_data="not_resolved"),
    )
    return kb

def rating_keyboard():
    kb = InlineKeyboardMarkup(row_width=5)
    for i in range(1,6):
        kb.insert(InlineKeyboardButton(str(i), callback_data=f"rating_{i}"))
    return kb

# --- Утилиты ---
def generate_ticket_code(length=6):
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        cursor.execute("SELECT code FROM tickets WHERE code = ?", (code,))
        if cursor.fetchone() is None:
            return code

async def send_farewell(user_id: int):
    phrase = random.choice(FAREWELL_PHRASES)
    await bot.send_message(user_id, phrase, reply_markup=main_menu())

# --- Хэндлеры ---

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(
        "🔐 Добро пожаловать в официальную поддержку LKN VPN!\n\n"
        "Я решаю типичные проблемы за 60 секунд:\n"
        "• Ошибки подключения\n"
        "• Низкая скорость\n"
        "• Настройка на устройствах\n"
        "• Вопросы о безопасности\n\n"
        "📌 Просто выберите интересующий пункт или опишите проблему.\n\n"
        "⚠️ Сложные вопросы передаю менеджеру\n"
        "⏱ Среднее время реакции: 2 минуты\n"
        "🛡 Ваш быстрый и бесплатный VPN - LKN!",
        reply_markup=main_menu()
    )

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.answer(
        "Доступные команды:\n"
        "/start - Запуск бота\n"
        "/help - Помощь\n"
        "/changepic - (Ответ на фото) смена фото профиля бота (только для админов)\n\n"
        "Используйте кнопки меню или опишите проблему."
    )

@dp.message_handler(commands=['changepic'])
async def cmd_changepic(message: types.Message):
    # Проверка прав: только админы группы или владелец (нужно дополнить по вашему сценарию)
    # В ЛС у бота нет прав менять фото, это работает в группах, где бот админ
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("Отправьте эту команду в ответ на фото, которое хотите установить в профиль бота.")
        return
    photo = message.reply_to_message.photo[-1]
    try:
        file = await bot.get_file(photo.file_id)
        downloaded = await bot.download_file(file.file_path)
        await bot.set_chat_photo(chat_id=message.chat.id, photo=downloaded)
        await message.answer("Фото профиля бота успешно обновлено!")
    except Exception as e:
        logger.error(f"Ошибка смены фото: {e}")
        await message.answer(f"Ошибка при смене фото профиля: {e}")

@dp.message_handler()
async def fallback_handler(message: types.Message):
    # На случай любого текста без callback
    await message.answer("Пожалуйста, используйте меню ниже или опишите проблему.", reply_markup=main_menu())

# --- Callback query handlers ---

@dp.callback_query_handler(lambda c: c.data == "how_connect")
async def process_how_connect(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await Form.waiting_for_device.set()
    await callback.message.answer("Какое устройство вы используете?", reply_markup=device_menu())

@dp.callback_query_handler(lambda c: c.data == "vpn_not_work")
async def process_vpn_not_work(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await Form.waiting_for_server.set()
    await callback.message.answer("Какой сервер вы используете?", reply_markup=server_menu())

@dp.callback_query_handler(lambda c: c.data == "logs")
async def process_logs(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("ВПН не собирает никаких данных, кроме даты регистрации в боте.", reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data == "paid_subscription")
async def process_paid_sub(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("Платная подписка планируется ориентировочно в октябре-ноябре 2025 года.", reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data == "ideas")
async def process_ideas(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await Form.waiting_for_idea.set()
    await callback.message.answer("Пожалуйста, напишите свои идеи и предложения.")

@dp.callback_query_handler(lambda c: c.data == "rf_server")
async def process_rf_server(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "РКН не блокирует данные серверов LKN VPN, что позволяет смотреть YouTube и другие сервисы без ограничений.",
        reply_markup=main_menu()
    )

# --- Обработка выбора устройства ---
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("device_"), state=Form.waiting_for_device)
async def process_device(callback: types.CallbackQuery, state: FSMContext):
    device = callback.data.split("_",1)[1]
    await callback.answer()
    text = ""
    if device in ["Android", "MacOS", "IOS"]:
        text = (
            "Инструкция по подключению VPN:\n"
            "1) Сгенерируйте ключ в боте.\n"
            "2) Скопируйте его.\n"
            "3) Скачайте приложение v2RayTun.\n"
            "4) Запустите приложение, нажмите '+' (в правом верхнем углу).\n"
            "5) Выберите 'Ручной ввод' и вставьте ключ.\n"
            "6) Выберите конфигурацию и нажмите 'Включить'.\n"
            "Готово! Приятного пользования."
        )
    elif device == "Windows":
        text = (
            "Инструкция по подключению VPN для Windows:\n"
            "1) Сгенерируйте ключ в боте.\n"
            "2) Скопируйте ключ.\n"
            "3) Скачайте приложение hiddify.\n"
            "4) Запустите, нажмите '+' и выберите 'Ручной ввод'.\n"
            "5) Вставьте ключ, выберите конфигурацию, нажмите 'Включить'.\n"
            "Готово! Приятного пользования."
        )
    else:
        await callback.message.answer("Пожалуйста, выберите устройство из списка.")
        return

    await callback.message.answer(text, reply_markup=resolve_menu())
    await Form.waiting_for_resolve.set()

# --- Обработка выбора сервера ---
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("server_"), state=Form.waiting_for_server)
async def process_server(callback: types.CallbackQuery, state: FSMContext):
    server = callback.data.split("_",1)[1]
    await state.update_data(chosen_server=server)
    await callback.answer()
    await callback.message.answer("В какой стране вы находитесь?", reply_markup=countries_menu())
    await Form.waiting_for_country.set()

# --- Обработка выбора страны ---
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("country_"), state=Form.waiting_for_country)
async def process_country(callback: types.CallbackQuery, state: FSMContext):
    country = callback.data.split("_",1)[1]
    data = await state.get_data()
    server = data.get("chosen_server")
    await callback.answer()

    if server == "Russia" and country == "Украина":
        await callback.message.answer(
            "Украинские операторы блокируют IP данного сервера.\n"
            "Рекомендуем использовать сервер Нидерланды 🇳🇱.",
            reply_markup=resolve_menu()
        )
    else:
        await callback.message.answer(
            "Проверьте:\n"
            "1) Интернет-соединение\n"
            "2) Обновление приложения\n"
            "3) Переключение авиарежима на 5 секунд\n"
            "4) Перезапуск устройства\n"
            "5) Выключение и включение VPN\n\n"
            "Для Windows: в приложении рядом с '+' нажмите 'Настройки' и выберите VPN вместо системного.",
            reply_markup=resolve_menu()
        )
    await Form.waiting_for_resolve.set()

# --- Обработка решения ---
@dp.callback_query_handler(lambda c: c.data in ["resolved","not_resolved"], state=Form.waiting_for_resolve)
async def process_resolve(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == "resolved":
        await callback.message.answer("Отлично! Пожалуйста, оцените качество обслуживания от 1 до 5.", reply_markup=rating_keyboard())
        await Form.waiting_for_rating.set()
    else:
        await callback.message.answer("Опишите вашу проблему подробно, чтобы мы могли помочь.")
        await Form.waiting_for_manager_problem.set()

# --- Обработка рейтинга ---
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("rating_"), state=Form.waiting_for_rating)
async def process_rating(callback: types.CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await callback.answer()
    if rating < 2:
        await callback.message.answer("Очень жаль, что возникли сложности. Пожалуйста, опишите, что именно не устроило.")
        await Form.waiting_for_problem_desc.set()
    else:
        await send_farewell(callback.from_user.id)
        await state.finish()

# --- Обработка описания проблемы после низкого рейтинга ---
@dp.message_handler(state=Form.waiting_for_problem_desc)
async def process_problem_desc(message: types.Message, state: FSMContext):
    desc = message.text.strip().lower()
    cursor.execute("SELECT id, count FROM problem_feedback WHERE description = ?", (desc,))
    row = cursor.fetchone()
    if row:
        pid, cnt = row
        cursor.execute("UPDATE problem_feedback SET count = ? WHERE id = ?", (cnt+1, pid))
    else:
        cursor.execute("INSERT INTO problem_feedback(description, count) VALUES (?, 1)", (desc,))
    conn.commit()
    await message.answer("Спасибо за обратную связь, мы обязательно улучшим сервис.")
    await send_farewell(message.from_user.id)
    await state.finish()

# --- Обработка подробного описания проблемы для менеджера ---
@dp.message_handler(state=Form.waiting_for_manager_problem)
async def process_manager_problem(message: types.Message, state: FSMContext):
    problem_text = message.text.strip()
    code = generate_ticket_code()
    cursor.execute(
        "INSERT INTO tickets (code, user_id, problem, status) VALUES (?, ?, ?, ?)",
        (code, message.from_user.id, problem_text, "new")
    )
    conn.commit()
    await message.answer(
        f"Спасибо, заявка принята.\n"
        f"Код обращения: {code}\n"
        "В течение 5 минут с вами свяжется менеджер.\n"
        "Пожалуйста, оцените качество обслуживания от 1 до 5.",
        reply_markup=rating_keyboard()
    )
    await Form.waiting_for_rating.set()

# --- Обработка идей ---
@dp.message_handler(state=Form.waiting_for_idea)
async def process_idea(message: types.Message, state: FSMContext):
    # Можно сохранить идеи в отдельную таблицу/файл при необходимости
    await message.answer("Спасибо за вашу идею! Мы обязательно рассмотрим её.\nПожалуйста, оцените качество обслуживания от 1 до 5.", reply_markup=rating_keyboard())
    await Form.waiting_for_rating.set()

# --- Команда для менеджера: /answer <код> <текст> ---
@dp.message_handler(lambda message: message.text and message.text.startswith("/answer"))
async def process_manager_answer(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Использование:\n/answer <код> <текст ответа>")
        return
    code, answer_text = parts[1], parts[2]
    cursor.execute("SELECT user_id FROM tickets WHERE code = ?", (code,))
    row = cursor.fetchone()
    if not row:
        await message.answer("Код обращения не найден.")
        return
    user_id = row[0]
    try:
        await bot.send_message(user_id, f"Ответ менеджера:\n{answer_text}")
        await bot.send_message(user_id, "Пожалуйста, нажмите 'Решено' или 'Не решено'.", reply_markup=resolve_menu())
        await message.answer("Ответ отправлен пользователю.")
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа менеджера: {e}")
        await message.answer("Не удалось отправить сообщение пользователю. Возможно, он заблокировал бота.")

# --- Запуск бота ---
if __name__ == "__main__":
    logger.info("Бот запущен и готов принимать сообщения...")
    executor.start_polling(dp)