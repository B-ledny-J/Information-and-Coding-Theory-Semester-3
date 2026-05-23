import os
import shelve
import uuid
from dotenv import load_dotenv
import telebot
from telebot import types
import hashlib

# 1. Завантажуємо змінні оточення
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Помилка: BOT_TOKEN не знайдено у файлі .env!")

bot = telebot.TeleBot(BOT_TOKEN)

# 2. Ініціалізуємо БД (shelve)
db = shelve.open("project_db", writeback=True)

if "users" not in db:
    db["users"] = {}
if "quizzes" not in db:
    db["quizzes"] = {}
db.sync()

# Тимчасова оперативна пам'ять для сесій редагування/створення тестів
# Сюди копіюються дані під час редагування, щоб можна було "Скасувати зміни"
edit_sessions = {}

def get_safe_text(message):
    # Повертає текст, якщо він є, або None, якщо це інший тип повідомлення
    if message.content_type == 'text':
        return message.text.strip()
    return None

# --- ГОЛОВНЕ МЕНЮ ТА СТАРТ ---
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("➕ Створити тест"), types.KeyboardButton("📋 Мої тести / Редагувати"))
    return markup


@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = str(message.from_user.id)
    display_name = message.from_user.first_name or f"ID_{user_id}"

    if user_id not in db["users"]:
        db["users"][user_id] = {"display_name": display_name, "passed_quizzes": {}}
        db.sync()

    bot.send_message(
        message.chat.id,
        f"👋 Привіт, {display_name}! Радий бачити тебе в ТІК Проєкті.\n"
        "Використовуй меню нижче для роботи з тестами:",
        reply_markup=get_main_menu()
    )


@bot.message_handler(func=lambda m: m.text in ["➕ Створити тест", "📋 Мої тести / Редагувати"])
def menu_router(message):
    if message.text == "➕ Створити тест":
        cmd_create(message)
    elif message.text == "📋 Мої тести / Редагувати":
        cmd_list_edit(message)

def get_user_quiz_count(user_id):
    return len([q_id for q_id, q in db["quizzes"].items() if q["creator_id"] == user_id])

# --- ФУНКЦІЯ /create ТА ІНІЦІАЛІЗАЦІЯ ---
def cmd_create(message):
    user_id = str(message.from_user.id)

    # ПЕРЕВІРКА ЛІМІТУ
    if get_user_quiz_count(user_id) >= 25:
        bot.send_message(message.chat.id, "❌ Ви досягли ліміту: максимум 25 тестів.")
        return

    msg = bot.send_message(message.chat.id, "📝 Введіть НАЗВУ для вашого нового тесту:")
    bot.register_next_step_handler(msg, process_init_title, user_id)


def process_init_title(message, user_id):
    title = get_safe_text()
    if not title:
        msg = bot.send_message(message.chat.id, "❌ Назва не може бути порожньою або бути НЕ текстом. Введіть ще раз:")
        bot.register_next_step_handler(msg, process_init_title, user_id)
        return

    quiz_id = str(uuid.uuid4())[:8]

    # Створюємо тимчасову чернетку в ОЗП (чернетка не збережеться в БД, поки не натиснуть "Зберегти")
    edit_sessions[user_id] = {
        "quiz_id": quiz_id,
        "title": title,
        "creator_id": user_id,
        "questions": [
            {"text": "Перше запитання (натисніть редагувати)", "options": ["Варіант 1", "Варіант 2"], "correct": 0}
        ],
        "current_q_idx": 0,  # Поточне обране запитання
        "is_new": True
    }
    show_editor_dashboard(message.chat.id, user_id)


# --- СПИСОК ДЛЯ РЕДАГУВАННЯ ---
def cmd_list_edit(message):
    user_id = str(message.from_user.id)
    my_quizzes = {q_id: q for q_id, q in db["quizzes"].items() if q["creator_id"] == user_id}

    if not my_quizzes:
        bot.send_message(message.chat.id, "📭 У вас ще немає створених тестів. Натисніть '➕ Створити тест'.")
        return

    bot.send_message(message.chat.id, "📋 Оберіть тест для редагування:")
    for q_id, q_data in my_quizzes.items():
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛠️ Редагувати цей тест", callback_data=f"ed_load_{q_id}"))
        bot.send_message(message.chat.id, f"🔸 Тест: *{q_data['title']}* (ID: `{q_id}`)", reply_markup=markup, parse_mode="Markdown")


# --- ІНТЕРАКТИВНИЙ ДАШБОРД РЕДАКТОРА ---
def show_editor_dashboard(chat_id, user_id, message_id=None):
    session = edit_sessions.get(user_id)
    if not session:
        bot.send_message(chat_id, "⌛ Сесію редагування закрито або застаріла.")
        return

    # Формування тексту статусу тесту
    text = f"🛠️ **РЕДАКТОР ТЕСТУ**\n"
    text += f"Назва: *{session['title']}*\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━\n"

    questions = session["questions"]
    curr_idx = session["current_q_idx"]

    if not questions:
        text += "⚠️ У тесті немає жодного запитання!\n"
    else:
        text += f"📋 Всього питань: {len(questions)}\n\n"
        for i, q in enumerate(questions):
            marker = "🎯" if i == curr_idx else "🔹"
            text += f"{marker} Питання {i + 1}: {q['text']}\n"
            if i == curr_idx:
                for j, opt in enumerate(q["options"]):
                    chk = "✅" if j == q["correct"] else "◻️"
                    text += f"      {chk} {j + 1}. {opt}\n"

        text += f"\n👉 *Поточне запитання для редагування: №{curr_idx + 1}*"

    # Генерація кнопок дій згідно з блок-схемою
    markup = types.InlineKeyboardMarkup(row_width=2)

    # Кнопки для тесту загалом
    markup.row(types.InlineKeyboardButton("📝 Редагувати назву тесту", callback_data="ed_action_title"))

    # Кнопки для питань
    markup.row(
        types.InlineKeyboardButton("➕ Додати запитання", callback_data="ed_action_addq"),
        types.InlineKeyboardButton("✏️ Виправити текст", callback_data="ed_action_editq")
    )
    markup.row(
        types.InlineKeyboardButton("🔢 Обрати інше поточне", callback_data="ed_action_selq"),
        types.InlineKeyboardButton("🗑️ Видалити поточне запитання", callback_data="ed_action_delq")
    )

    # Кнопки для відповідей
    markup.row(
        types.InlineKeyboardButton("➕ Додати відповідь", callback_data="ed_action_addans"),
        types.InlineKeyboardButton("🗑️ Видалити відповідь", callback_data="ed_action_delans")
    )
    markup.row(types.InlineKeyboardButton("🎯 Обрати/Змінити правильну", callback_data="ed_action_setcorr"))

    # Кнопка для встановлення паролю
    markup.add(types.InlineKeyboardButton("🔑 Пароль", callback_data="ed_action_password"))

    # Фінальні кнопки (Збереження / Скасування)
    markup.row(
        types.InlineKeyboardButton("💾 ЗБЕРЕГТИ ЗМІНИ", callback_data="ed_action_save"),
        types.InlineKeyboardButton("❌ Скасувати зміни", callback_data="ed_action_cancel")
    )

    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
        except:
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")


# --- ОБРОБКА ДІЙ КОРИСТУВАЧА (CALLBACK QUERIES) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("ed_"))
def handle_editor_callbacks(call):
    user_id = str(call.from_user.id)
    chat_id = call.message.chat.id

    # Завантаження існуючого тесту в редактор
    if call.data.startswith("ed_load_"):
        quiz_id = call.data.split("_")[2]
        orig = db["quizzes"].get(quiz_id)
        if orig:
            # Клонуємо структуру в ОЗП для безпечного редагування
            edit_sessions[user_id] = {
                "quiz_id": quiz_id,
                "title": orig["title"],
                "creator_id": orig["creator_id"],
                "questions": [q.copy() for q in orig["questions"]],
                "current_q_idx": 0,
                "is_new": False
            }
            bot.answer_callback_query(call.id, "Тест завантажено в редактор")
            show_editor_dashboard(chat_id, user_id)
        return

    if call.data.startswith("ed_pwd_") or call.data == "ed_action_back":
        handle_password_actions(call)  # Викликаємо окрему функцію для паролів
        return

    session = edit_sessions.get(user_id)
    if not session:
        bot.answer_callback_query(call.id, "Сесія не знайдена.")
        return

    action = call.data.replace("ed_action_", "")
    bot.answer_callback_query(call.id)

    # 1. Редагувати назву тесту
    if action == "title":
        msg = bot.send_message(chat_id, "Введіть НОВУ назву для цього тесту:")
        bot.register_next_step_handler(msg, input_edit_title, user_id)

    # 2. Додати нове запитання
    elif action == "addq":
        msg = bot.send_message(chat_id, " Введіть ТЕКСТ нового запитання:")
        bot.register_next_step_handler(msg, input_add_question, user_id)

    # 3. Виправити поточне запитання
    elif action == "editq":
        if not session["questions"]:
            bot.send_message(chat_id, "❌ Немає питань для редагування.")
            return
        msg = bot.send_message(chat_id, f" Введіть НОВИЙ текст для запитання №{session['current_q_idx'] + 1}:")
        bot.register_next_step_handler(msg, input_edit_question, user_id)

    # 4. Обрати інше запитання як поточне
    elif action == "selq":
        if not session["questions"]:
            bot.send_message(chat_id, "❌ Список питань порожній.")
            return
        msg = bot.send_message(chat_id,
                               f"🔢 Введіть номер запитання, яке зробити поточним (1-{len(session['questions'])}):")
        bot.register_next_step_handler(msg, input_select_question, user_id)

    # 5. Видалити поточне запитання
    elif action == "delq":
        if not session["questions"]:  # Запитання існують? (Hi)
            bot.send_message(chat_id, "⚠️ Запитання відсутні. Нічого видаляти.")
            return

        # Видалення запитання
        del session["questions"][session["current_q_idx"]]
        session["current_q_idx"] = 0  # Обрання першого запитання поточним
        show_editor_dashboard(chat_id, user_id)

    # 6. Додати відповідь
    elif action == "addans":
        if not session["questions"]:
            bot.send_message(chat_id, "❌ Спочатку додайте запитання!")
            return
        msg = bot.send_message(chat_id, "📝 Введіть текст нової відповіді:")
        bot.register_next_step_handler(msg, input_add_answer, user_id)

    # 7. Видалити відповідь
    elif action == "delans":
        if not session["questions"]: return
        q = session["questions"][session["current_q_idx"]]

        # Відповідей більше ніж 2?
        if len(q["options"]) <= 2:
            bot.send_message(chat_id, "❌ Помилка! У питанні має залишатися мінімум 2 відповіді.")
            return

        msg = bot.send_message(chat_id, f"🗑️ Введіть номер відповіді для видалення (1-{len(q['options'])}):")
        bot.register_next_step_handler(msg, input_delete_answer, user_id)

    # 8. Обрати/змінити правильну відповідь
    elif action == "setcorr":
        if not session["questions"]: return
        q = session["questions"][session["current_q_idx"]]
        msg = bot.send_message(chat_id, f"🎯 Введіть номер правильної відповіді (1-{len(q['options'])}):")
        bot.register_next_step_handler(msg, input_set_correct, user_id)

    # Додати пароль
    elif action == "password":
        # Отримуємо дані з БД (якщо тест ще не збережено, дивимось у тимчасову сесію)
        quiz_id = session["quiz_id"]
        # Перевіряємо в БД, чи вже є такий тест, щоб дізнатися статус пароля
        quiz_data = db["quizzes"].get(quiz_id, {})
        is_protected = quiz_data.get("is_password_protected", False)

        markup = types.InlineKeyboardMarkup()
        if is_protected:
            markup.row(types.InlineKeyboardButton("🔄 Змінити пароль", callback_data="ed_pwd_set"))
            markup.row(types.InlineKeyboardButton("🗑️ Видалити пароль", callback_data="ed_pwd_del"))
        else:
            markup.row(types.InlineKeyboardButton("➕ Встановити пароль", callback_data="ed_pwd_set"))

        markup.row(types.InlineKeyboardButton("🔙 Назад до меню", callback_data="ed_action_back"))
        bot.edit_message_text("🔑 **Керування паролем тесту:**", chat_id, call.message.message_id, reply_markup=markup,
                              parse_mode="Markdown")

    # 9. СКАСУВАТИ ЗМІНИ
    elif action == "cancel":
        if user_id in edit_sessions:
            del edit_sessions[user_id]  # Видалення тимчасових змін з ОЗП
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, "❌ Редагування скасовано. Усі незбережені зміни видалено.",
                         reply_markup=get_main_menu())

    # 10. ЗБЕРЕГТИ ЗМІНИ
    elif action == "save":
        # Валідація перед збереженням
        if not session["questions"]:
            bot.send_message(chat_id, "❌ Не можна зберегти тест без питань!")
            return

        # Перевірка на унікальність ID при створенні нового тесту
        quiz_id = session["quiz_id"]
        if session["is_new"]:
            while quiz_id in db["quizzes"]:
                quiz_id = str(uuid.uuid4())[:8]
            session["quiz_id"] = quiz_id

            # Ініціалізація нових полів для НОВОГО тесту
            new_test_data = {
                "title": session["title"],
                "creator_id": session["creator_id"],
                "questions": session["questions"],
                "rating": [],  # Порожній список для рейтингу
                "password_hash": None,  # Хеш пароля (None, якщо немає)
                "is_password_protected": False
            }
            db["quizzes"][quiz_id] = new_test_data
        else:
            # Оновлення існуючого (пароль та рейтинг не чіпаємо)
            db["quizzes"][quiz_id].update({
                "title": session["title"],
                "questions": session["questions"]
            })

        db.sync()

        # Перевірка: Є новим тестом?
        if session["is_new"]:
            bot.send_message(chat_id, f"🎉 Тест успішно створено! ID: `{quiz_id}`", parse_mode="Markdown",
                             reply_markup=get_main_menu())
        else:
            bot.send_message(chat_id, "💾 Зміни успішно збережено в оригінальний тест!",
                             reply_markup=get_main_menu())

        del edit_sessions[user_id]
        bot.delete_message(chat_id, call.message.message_id)


# --- ОБРОБКА ДІЙ З ПАРОЛЕМ ---
def handle_password_actions(call):
    user_id = str(call.from_user.id)
    chat_id = call.message.chat.id
    session = edit_sessions.get(user_id)

    if not session:
        bot.answer_callback_query(call.id, "Сесія не знайдена.")
        return

    # Обробка кнопки "Назад"
    if call.data == "ed_action_back":
        show_editor_dashboard(chat_id, user_id, call.message.message_id)
        return

    # Обробка встановлення/зміни пароля
    if call.data == "ed_pwd_set":
        msg = bot.send_message(chat_id, "🔐 Введіть новий пароль для тесту:")
        bot.register_next_step_handler(msg, process_set_password, user_id)

    # Обробка видалення пароля
    elif call.data == "ed_pwd_del":
        quiz_id = session["quiz_id"]
        # Якщо тест вже в БД, оновлюємо його
        if quiz_id in db["quizzes"]:
            db["quizzes"][quiz_id].update({
                "is_password_protected": False,
                "password_hash": None
            })
            db.sync()

        bot.answer_callback_query(call.id, "Пароль видалено")
        show_editor_dashboard(chat_id, user_id, call.message.message_id)


def process_set_password(message, user_id):
    password = message.text.strip()
    session = edit_sessions.get(user_id)
    if not session: return

    quiz_id = session["quiz_id"]
    hashed = hash_password(password)

    # Оновлюємо базу даних
    if quiz_id in db["quizzes"]:
        db["quizzes"][quiz_id].update({
            "is_password_protected": True,
            "password_hash": hashed
        })
        db.sync()

    bot.send_message(message.chat.id, "✅ Пароль успішно встановлено!")
    show_editor_dashboard(message.chat.id, user_id)

# --- ФУНКЦІЇ ВВЕДЕННЯ ТЕКСТУ (NEXT STEP HANDLERS) ---

def input_edit_title(message, user_id):
    title = message.text.strip()
    if title:
        edit_sessions[user_id]["title"] = title
    show_editor_dashboard(message.chat.id, user_id)


def input_add_question(message, user_id):
    text = message.text.strip()
    if text:
        new_q = {"text": text, "options": ["Варіант 1", "Варіант 2"], "correct": 0}
        edit_sessions[user_id]["questions"].append(new_q)
        # Автоматично робимо нове запитання поточним
        edit_sessions[user_id]["current_q_idx"] = len(edit_sessions[user_id]["questions"]) - 1
    show_editor_dashboard(message.chat.id, user_id)


def input_edit_question(message, user_id):
    text = message.text.strip()
    if text:
        idx = edit_sessions[user_id]["current_q_idx"]
        edit_sessions[user_id]["questions"][idx]["text"] = text
    show_editor_dashboard(message.chat.id, user_id)


def input_select_question(message, user_id):
    try:
        num = int(message.text.strip()) - 1
        if 0 <= num < len(edit_sessions[user_id]["questions"]):
            edit_sessions[user_id]["current_q_idx"] = num
        else:
            bot.send_message(message.chat.id, "❌ Неправильний номер запитання.")
    except:
        bot.send_message(message.chat.id, "❌ Потрібно ввести число.")
    show_editor_dashboard(message.chat.id, user_id)


def input_add_answer(message, user_id):
    text = message.text.strip()
    if text:
        idx = edit_sessions[user_id]["current_q_idx"]
        edit_sessions[user_id]["questions"][idx]["options"].append(text)
    show_editor_dashboard(message.chat.id, user_id)


def input_delete_answer(message, user_id):
    try:
        idx = edit_sessions[user_id]["current_q_idx"]
        q = edit_sessions[user_id]["questions"][idx]
        num = int(message.text.strip()) - 1

        if 0 <= num < len(q["options"]):
            del q["options"][num]
            # Захист від виходу за межі індексу правильної відповіді
            q["correct"] = 0
        else:
            bot.send_message(message.chat.id, "❌ Неправильний номер відповіді.")
    except:
        bot.send_message(message.chat.id, "❌ Потрібно ввести число.")
    show_editor_dashboard(message.chat.id, user_id)


def input_set_correct(message, user_id):
    try:
        idx = edit_sessions[user_id]["current_q_idx"]
        q = edit_sessions[user_id]["questions"][idx]
        num = int(message.text.strip()) - 1

        if 0 <= num < len(q["options"]):
            q["correct"] = num  # Маркування відповіді як правильної
        else:
            bot.send_message(message.chat.id, "❌ Такого номера відповіді не існує.")
    except:
        bot.send_message(message.chat.id, "❌ Потрібно ввести число.")
    show_editor_dashboard(message.chat.id, user_id)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# --- ЗАПУСК БОТА ---
if __name__ == "__main__":
    try:
        bot.infinity_polling()
    finally:
        db.close()
        print("Базу даних безпечно закрито.")