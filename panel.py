import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# ====== НАСТРОЙКИ ======
BOT_TOKEN = "9064511972:AAH5NtDMxkz37QcQcRqs1I3JHfHlWOQ97eA"
BOT_USERNAME = "ruvierapanelbot"
OWNERS = [8941873700, 8984825522]
INVITE_LINK = "https://t.me/+1sEzRWN8OZwzMWUy"
DB_PATH = "bot.db"
# =======================

logging.basicConfig(level=logging.INFO)
router = Router()

# ---------- БАЗА ----------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS apps (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, full_name TEXT,
            source TEXT, work_time TEXT, status TEXT DEFAULT 'pending', decided_by INTEGER
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS owner_msgs (app_id INTEGER, chat_id INTEGER, message_id INTEGER)""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT,
            wallet TEXT, show_username INTEGER DEFAULT 0,
            profits INTEGER DEFAULT 0, profit_sum REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            referrer_id INTEGER DEFAULT NULL, refs_count INTEGER DEFAULT 0,
            mentor_id INTEGER DEFAULT NULL
        )""")
        
        for col in ["mentor_id INTEGER DEFAULT NULL", "referrer_id INTEGER DEFAULT NULL", "refs_count INTEGER DEFAULT 0"]:
            try:
                c.execute(f"ALTER TABLE users ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass

        c.execute("DROP TABLE IF EXISTS mentors")
        c.execute("""CREATE TABLE mentors (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            display_name TEXT,
            description TEXT
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS mentor_apps (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, mentor_id INTEGER,
            status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)""")
        default_settings = {
            "menu_photo": "",
            "menu_text": "Главное меню\n\nВыберите нужный раздел ниже:",
            "profile_text_header": "Ваш профиль\n\n",
            "about_text": (
                "Приветствую начинающий воркер! Ты попал в Ruviera Team. "
                "Здесь дружный коллектив, мы сможем тебя обучить ворку, и если у тебя еще не было профитов, "
                "то обязательно это исправим и доведем до первого профита!\n\n"
                "Ruviera Team"
            ),
            "mentor_default_desc": (
                "Что ты получаешь:\n"
                "Наставлю вас на первый профит, научу азам ворка, дам авторскую методику как надо воркать.\n\n"
                "Условия: с первых трех профитов 10% уходят наставнику."
            ),
            # Названия кнопок главного меню
            "btn_profile": "Профиль",
            "btn_refs": "Рефералы",
            "btn_profits": "Мои профиты",
            "btn_bots": "Боты",
            "btn_mentor": "Наставник",
            "btn_about": "О проекте"
        }
        for k, v in default_settings.items():
            c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

def get_setting(key: str) -> str:
    with db() as c:
        row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else ""

def set_setting(key: str, value: str):
    with db() as c:
        c.execute("UPDATE settings SET value=? WHERE key=?", (value, key))

def ensure_user(user, referrer_id=None):
    username = f"@{user.username}" if user.username else None
    with db() as c:
        row = c.execute("SELECT user_id FROM users WHERE user_id=?", (user.id,)).fetchone()
        if not row:
            c.execute("INSERT INTO users (user_id, username, full_name, referrer_id) VALUES (?, ?, ?, ?)",
                      (user.id, username, user.full_name, referrer_id))
            if referrer_id and referrer_id != user.id:
                c.execute("UPDATE users SET refs_count = refs_count + 1 WHERE user_id=?", (referrer_id,))
        else:
            c.execute("UPDATE users SET username=?, full_name=? WHERE user_id=?", (username, user.full_name, user.id))

def get_status(user_id: int) -> str:
    return "Владелец" if user_id in OWNERS else "Воркер"

def get_place_in_top(user_id: int) -> str:
    with db() as c:
        rows = c.execute("SELECT user_id FROM users ORDER BY profits DESC, profit_sum DESC").fetchall()
    for i, r in enumerate(rows, start=1):
        if r["user_id"] == user_id:
            return f"{i}" if i <= 75 else "75+"
    return "—"

# ---------- КЛАВИАТУРЫ ----------
def decision_kb(app_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Одобрить", callback_data=f"ok:{app_id}"),
        InlineKeyboardButton(text="Отклонить", callback_data=f"no:{app_id}"),
    ]])

def main_menu_kb(user_id: int) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text=get_setting("btn_profile"), callback_data="menu_profile")],
        [
            InlineKeyboardButton(text=get_setting("btn_refs"), callback_data="menu_refs"),
            InlineKeyboardButton(text=get_setting("btn_profits"), callback_data="menu_profits"),
        ],
        [
            InlineKeyboardButton(text=get_setting("btn_bots"), callback_data="menu_bots"),
            InlineKeyboardButton(text=get_setting("btn_mentor"), callback_data="menu_mentor"),
        ],
        [InlineKeyboardButton(text=get_setting("btn_about"), callback_data="menu_about")],
    ]
    if user_id in OWNERS:
        kb.append([InlineKeyboardButton(text="Настройки", callback_data="admin_settings")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить/изменить кошелёк", callback_data="wallet_edit")],
        [InlineKeyboardButton(text="Показывать ник в профилях", callback_data="toggle_username")],
        [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")],
    ])

def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]])

def admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить фото", callback_data="admin_photo_menu")],
        [InlineKeyboardButton(text="Изменить текст меню", callback_data="admin_text_menu")],
        [InlineKeyboardButton(text="Изменить названия кнопок", callback_data="admin_btn_names")],
        [InlineKeyboardButton(text="Добавить наставника", callback_data="admin_add_mentor")],
        [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")],
    ])

def admin_btn_names_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"1. {get_setting('btn_profile')}", callback_data="edit_btn:btn_profile")],
        [InlineKeyboardButton(text=f"2. {get_setting('btn_refs')}", callback_data="edit_btn:btn_refs")],
        [InlineKeyboardButton(text=f"3. {get_setting('btn_profits')}", callback_data="edit_btn:btn_profits")],
        [InlineKeyboardButton(text=f"4. {get_setting('btn_bots')}", callback_data="edit_btn:btn_bots")],
        [InlineKeyboardButton(text=f"5. {get_setting('btn_mentor')}", callback_data="edit_btn:btn_mentor")],
        [InlineKeyboardButton(text=f"6. {get_setting('btn_about')}", callback_data="edit_btn:btn_about")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_settings")],
    ])

def mentors_kb() -> InlineKeyboardMarkup:
    kb = []
    with db() as c:
        rows = c.execute("SELECT user_id, username, display_name FROM mentors").fetchall()
    for r in rows:
        name = r["display_name"] or r["username"] or f"ID {r['user_id']}"
        kb.append([InlineKeyboardButton(text=f"{name}", callback_data=f"mentor_view:{r['user_id']}")])
    kb.append([InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def mentor_view_kb(mentor_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подать заявку", callback_data=f"mentor_apply:{mentor_id}")],
        [InlineKeyboardButton(text="К списку", callback_data="menu_mentor")],
    ])

def mentor_decision_kb(mapp_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Принять", callback_data=f"mok:{mapp_id}"),
        InlineKeyboardButton(text="Отклонить", callback_data=f"mno:{mapp_id}"),
    ]])

def mentor_profile_edit_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить описание", callback_data="mentor_edit_desc")],
        [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")],
    ])

# ---------- СОСТОЯНИЯ ----------
class Form(StatesGroup):
    source = State()
    work_time = State()
    wallet = State()
    admin_upload_photo = State()
    admin_edit_text = State()
    admin_edit_btn = State()
    admin_add_mentor = State()
    mentor_edit_desc = State()

# ---------- ХЕЛПЕР ДЛЯ ОТПРАВКИ С КАРТИНКОЙ ----------
async def send_with_photo(message: Message, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode="HTML"):
    photo = get_setting("menu_photo")
    if photo:
        try:
            await message.answer_photo(photo=photo, caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)

# ---------- ТЕКСТЫ ----------
def profile_text(user_id: int) -> str:
    with db() as c:
        u = c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not u:
        return "Профиль не найден."

    nick = u["username"] or "нет username"
    wallet = u["wallet"] or "не указан"
    status = get_status(user_id)
    show = "открыт" if u["show_username"] else "скрыт"
    place = get_place_in_top(user_id)
    header = get_setting("profile_text_header")

    return (
        f"{header}"
        f"Ник: {nick}\n"
        f"ID: {user_id}\n"
        f"Статус: {status}\n"
        f"Ник в профитах: {show}\n\n"
        f"Кошелёк: {wallet}\n\n"
        "Статистика:\n"
        f"Место в топе: {place}\n"
        f"Профитов: {u['profits']}\n"
        f"Сумма профитов: {u['profit_sum']} Gram"
    )

def get_ref_text(user_id: int) -> str:
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    with db() as c:
        u = c.execute("SELECT refs_count FROM users WHERE user_id=?", (user_id,)).fetchone()
        count = u["refs_count"] if u else 0
    return (
        "Ваша реферальная ссылка:\n\n"
        f"<code>{ref_link}</code>\n\n"
        "Условия:\n"
        "- За каждого приглашенного человека +0.15 TON\n"
        "- Вывод доступен от 5 человек\n\n"
        f"Вы пригласили: {count} чел.\n\n"
        "ВНИМАНИЕ!\n"
        "Накрутка ботов, вторых аккаунтов ЗАПРЕЩЕНА.\n"
        "Все приглашения будут строго проверяться администраторами."
    )

def get_profits_text(user_id: int) -> str:
    with db() as c:
        u = c.execute("SELECT profits, profit_sum, refs_count FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not u:
        return "Данные не найдены."
    return (
        "Мои профиты\n\n"
        f"Всего профитов: {u['profits']}\n"
        f"Заработано: {u['profit_sum']} Gram\n\n"
        f"Приглашено рефералов: {u['refs_count']}\n\n"
        "Здесь отображается ваша личная статистика."
    )

# ---------- ГЛАВНОЕ МЕНЮ ----------
async def send_main_menu(message: Message, user_id: int):
    text = get_setting("menu_text")
    kb = main_menu_kb(user_id)
    await send_with_photo(message, text, kb)

# ---------- СТАРТ ----------
@router.message(CommandStart())
async def start(message: Message, state: FSMContext, command: CommandObject):
    ref_id = None
    if command.args and command.args.startswith("ref_"):
        try:
            ref_id = int(command.args.replace("ref_", ""))
        except ValueError:
            pass
    ensure_user(message.from_user, referrer_id=ref_id)
    await state.clear()

    with db() as c:
        row = c.execute("SELECT status FROM apps WHERE user_id=? ORDER BY id DESC LIMIT 1", (message.from_user.id,)).fetchone()

    if row:
        if row["status"] == "pending":
            return await send_with_photo(message, "Ваша заявка уже на рассмотрении, ожидайте.")
        if row["status"] == "approved":
            return await send_main_menu(message, message.from_user.id)
        if row["status"] == "rejected":
            return await send_with_photo(message, "Ваша заявка была отклонена.")

    await state.set_state(Form.source)
    await send_with_photo(message, "Привет! Откуда узнали о нас?")

@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    ensure_user(message.from_user)
    await send_main_menu(message, message.from_user.id)

# ---------- АНКЕТА ----------
@router.message(Form.source, F.text)
async def get_source(message: Message, state: FSMContext):
    await state.update_data(source=message.text.strip())
    await state.set_state(Form.work_time)
    await send_with_photo(message, "Сколько времени готовы уделять работе?")

@router.message(Form.work_time, F.text)
async def get_time(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    user = message.from_user
    username = f"@{user.username}" if user.username else "нет username"

    with db() as c:
        cur = c.execute(
            "INSERT INTO apps (user_id, username, full_name, source, work_time) VALUES (?, ?, ?, ?, ?)",
            (user.id, username, user.full_name, data["source"], message.text.strip()),
        )
        app_id = cur.lastrowid

    text = (
        f"Новая заявка #{app_id}\n\n"
        f"{user.full_name}\n{username}\n{user.id}\n\n"
        f"Откуда узнал: {data['source']}\nВремя на работу: {message.text.strip()}"
    )

    for owner in OWNERS:
        try:
            m = await bot.send_message(owner, text, reply_markup=decision_kb(app_id))
            with db() as c:
                c.execute("INSERT INTO owner_msgs VALUES (?, ?, ?)", (app_id, m.chat.id, m.message_id))
        except Exception as e:
            logging.error(f"Не удалось отправить владельцу {owner}: {e}")

    await send_with_photo(message, "Заявка отправлена! Ожидайте решения.")

# ---------- ПРОФИЛЬ ----------
@router.callback_query(F.data == "menu_profile")
async def menu_profile(call: CallbackQuery):
    await send_with_photo(call.message, profile_text(call.from_user.id), profile_kb())
    await call.answer()

@router.callback_query(F.data == "wallet_edit")
async def wallet_edit(call: CallbackQuery, state: FSMContext):
    await state.set_state(Form.wallet)
    await send_with_photo(call.message, "Введите адрес вашего кошелька (например TON-адрес, начинается с UQ... или EQ...).\n\nОтмена: /menu")
    await call.answer()

@router.message(Form.wallet, F.text)
async def wallet_save(message: Message, state: FSMContext):
    wallet = message.text.strip()
    if not (len(wallet) >= 40 and wallet[:2].upper() in ("UQ", "EQ")):
        return await send_with_photo(message, "Похоже, это не TON-адрес. Попробуйте ещё раз или отправьте /menu для отмены.")
    with db() as c:
        c.execute("UPDATE users SET wallet=? WHERE user_id=?", (wallet, message.from_user.id))
    await state.clear()
    await send_with_photo(message, "Кошелёк сохранён!\n\n" + profile_text(message.from_user.id), profile_kb())

@router.callback_query(F.data == "toggle_username")
async def toggle_username(call: CallbackQuery):
    with db() as c:
        u = c.execute("SELECT show_username FROM users WHERE user_id=?", (call.from_user.id,)).fetchone()
        new_val = 0 if u["show_username"] else 1
        c.execute("UPDATE users SET show_username=? WHERE user_id=?", (new_val, call.from_user.id))
    await send_with_photo(call.message, profile_text(call.from_user.id), profile_kb())
    await call.answer("Обновлено")

# ---------- РЕФЕРАЛЫ ----------
@router.callback_query(F.data == "menu_refs")
async def menu_refs(call: CallbackQuery):
    await send_with_photo(call.message, get_ref_text(call.from_user.id), back_to_menu_kb())
    await call.answer()

# ---------- МОИ ПРОФИТЫ ----------
@router.callback_query(F.data == "menu_profits")
async def menu_profits(call: CallbackQuery):
    await send_with_photo(call.message, get_profits_text(call.from_user.id), back_to_menu_kb())
    await call.answer()

# ---------- О ПРОЕКТЕ ----------
@router.callback_query(F.data == "menu_about")
async def menu_about(call: CallbackQuery):
    await send_with_photo(call.message, get_setting("about_text"), back_to_menu_kb())
    await call.answer()

# ---------- НАСТАВНИКИ ----------
@router.callback_query(F.data == "menu_mentor")
async def menu_mentor(call: CallbackQuery):
    await send_with_photo(call.message, "Наставники Ruviera Team\n\nВыберите наставника, к которому хотите подать заявку:", mentors_kb())
    await call.answer()

@router.callback_query(F.data.startswith("mentor_view:"))
async def mentor_view(call: CallbackQuery):
    mentor_id = int(call.data.split(":")[1])
    with db() as c:
        m = c.execute("SELECT * FROM mentors WHERE user_id=?", (mentor_id,)).fetchone()
    if not m:
        return await call.answer("Наставник не найден.", show_alert=True)
    name = m["display_name"] or m["username"] or f"ID {mentor_id}"
    desc = m["description"] if m["description"] else get_setting("mentor_default_desc")
    text = (
        f"Наставник {name}\n\n"
        f"{desc}\n\n"
        "Готов? Подай заявку — наставник примет или отклонит."
    )
    await send_with_photo(call.message, text, mentor_view_kb(mentor_id))
    await call.answer()

@router.callback_query(F.data.startswith("mentor_apply:"))
async def mentor_apply(call: CallbackQuery, bot: Bot):
    mentor_id = int(call.data.split(":")[1])
    user_id = call.from_user.id
    if mentor_id == user_id:
        return await call.answer("Вы не можете подать заявку самому себе.", show_alert=True)

    with db() as c:
        existing = c.execute("SELECT id FROM mentor_apps WHERE user_id=? AND status='pending'", (user_id,)).fetchone()
        if existing:
            return await call.answer("У вас уже есть активная заявка.", show_alert=True)
        cur = c.execute("INSERT INTO mentor_apps (user_id, mentor_id) VALUES (?, ?)", (user_id, mentor_id))
        mapp_id = cur.lastrowid

    user_info = f"{call.from_user.full_name}\n@{call.from_user.username or 'нет'}\n{user_id}"
    notification = f"Новая заявка к вам на наставничество\n\n{user_info}"
    
    try:
        await bot.send_message(mentor_id, notification, reply_markup=mentor_decision_kb(mapp_id))
    except Exception as e:
        await call.answer("Наставник недоступен (не нажал /start у бота).", show_alert=True)
        logging.error(f"Ошибка отправки наставнику {mentor_id}: {e}")
        return

    await send_with_photo(call.message, "Ваша заявка отправлена наставнику! Ожидайте.", back_to_menu_kb())
    await call.answer()

@router.callback_query(F.data.regexp(r"^m(ok|no):\d+$"))
async def mentor_decide(call: CallbackQuery, bot: Bot):
    action, mapp_id = call.data[1:].split(":")
    mapp_id = int(mapp_id)

    with db() as c:
        mapp = c.execute("SELECT * FROM mentor_apps WHERE id=?", (mapp_id,)).fetchone()
        if not mapp:
            return await call.answer("Заявка не найдена", show_alert=True)
        if mapp["status"] != "pending":
            return await call.answer("Уже обработана", show_alert=True)
        if call.from_user.id != mapp["mentor_id"] and call.from_user.id not in OWNERS:
            return await call.answer("Эта заявка не для вас!", show_alert=True)

        status = "approved" if action == "ok" else "rejected"
        c.execute("UPDATE mentor_apps SET status=? WHERE id=?", (status, mapp_id))
        if status == "approved":
            c.execute("UPDATE users SET mentor_id=? WHERE user_id=?", (mapp["mentor_id"], mapp["user_id"]))

    try:
        if status == "approved":
            await bot.send_message(mapp["user_id"], "Ваша заявка на наставничество одобрена! Наставник свяжется с вами.")
        else:
            await bot.send_message(mapp["user_id"], "Ваша заявка на наставничество отклонена.")
    except Exception as e:
        logging.error(f"Не удалось написать пользователю: {e}")

    label = "ОДОБРЕНО" if status == "approved" else "ОТКЛОНЕНО"
    try:
        await call.message.edit_text(call.message.text + f"\n\n{label}")
    except Exception:
        pass
    await call.answer("Готово")

# ---------- ЛИЧНЫЙ КАБИНЕТ НАСТАВНИКА ----------
@router.message(Command("mentor_profile"))
async def mentor_panel(message: Message):
    with db() as c:
        m = c.execute("SELECT * FROM mentors WHERE user_id=?", (message.from_user.id,)).fetchone()
    if not m:
        return await send_with_photo(message, "Вы не являетесь наставником.")
    name = m["display_name"] or m["username"] or f"ID {m['user_id']}"
    desc = m["description"] if m["description"] else "пока не заполнено (используется стандартное)"
    await send_with_photo(
        message,
        f"Профиль наставника\n\n"
        f"Ник: {name}\n"
        f"Описание:\n{desc}\n\n"
        "Вы можете изменить описание, чтобы воркеры видели его.",
        mentor_profile_edit_kb()
    )

@router.callback_query(F.data == "mentor_edit_desc")
async def mentor_edit_desc(call: CallbackQuery, state: FSMContext):
    with db() as c:
        m = c.execute("SELECT user_id FROM mentors WHERE user_id=?", (call.from_user.id,)).fetchone()
    if not m:
        return await call.answer("Вы не наставник.", show_alert=True)
    await state.set_state(Form.mentor_edit_desc)
    await send_with_photo(call.message, "Отправьте новый текст описания вашего профиля наставника.\n\nОтмена: /menu")
    await call.answer()

@router.message(Form.mentor_edit_desc, F.text)
async def mentor_save_desc(message: Message, state: FSMContext):
    with db() as c:
        m = c.execute("SELECT user_id FROM mentors WHERE user_id=?", (message.from_user.id,)).fetchone()
    if not m:
        await state.clear()
        return await send_with_photo(message, "Вы не наставник.")
    with db() as c:
        c.execute("UPDATE mentors SET description=? WHERE user_id=?", (message.text.strip(), message.from_user.id))
    await state.clear()
    await send_with_photo(message, "Описание обновлено! Воркеры увидят его при выборе.", back_to_menu_kb())

# ---------- АДМИНКА ----------
@router.callback_query(F.data == "admin_settings")
async def admin_settings(call: CallbackQuery):
    if call.from_user.id not in OWNERS:
        return await call.answer("Нет доступа", show_alert=True)
    await send_with_photo(call.message, "Настройки бота\n\nВыберите:", admin_kb())
    await call.answer()

@router.callback_query(F.data == "admin_btn_names")
async def admin_btn_names(call: CallbackQuery):
    if call.from_user.id not in OWNERS:
        return await call.answer("Нет доступа", show_alert=True)
    await send_with_photo(call.message, "Выберите кнопку, название которой хотите изменить:", admin_btn_names_kb())
    await call.answer()

@router.callback_query(F.data.startswith("edit_btn:"))
async def edit_btn_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in OWNERS:
        return await call.answer("Нет доступа", show_alert=True)
    key = call.data.split(":")[1]
    await state.set_state(Form.admin_edit_btn)
    await state.update_data(btn_key=key)
    current = get_setting(key)
    await send_with_photo(call.message, f"Текущее название: {current}\n\nОтправьте новое название кнопки.\n\nОтмена: /menu")
    await call.answer()

@router.message(Form.admin_edit_btn, F.text)
async def admin_btn_save(message: Message, state: FSMContext):
    if message.from_user.id not in OWNERS:
        return
    data = await state.get_data()
    key = data.get("btn_key")
    if not key:
        await state.clear()
        return await send_with_photo(message, "Ошибка сессии. Начните заново: /menu")
    set_setting(key, message.text.strip())
    await state.clear()
    await send_with_photo(message, "Название кнопки обновлено! Проверьте /menu", back_to_menu_kb())

@router.callback_query(F.data == "admin_add_mentor")
async def admin_add_mentor(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in OWNERS:
        return await call.answer("Нет доступа", show_alert=True)
    await state.set_state(Form.admin_add_mentor)
    await send_with_photo(
        call.message,
        "Отправьте ID пользователя, которого хотите сделать наставником.\n\n"
        "Важно: человек должен хотя бы раз нажать /start у бота.\n\n"
        "Отмена: /menu"
    )
    await call.answer()

@router.message(Form.admin_add_mentor, F.text)
async def admin_add_mentor_save(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id not in OWNERS:
        return
    try:
        mentor_id = int(message.text.strip())
    except ValueError:
        return await send_with_photo(message, "ID должен быть числом. Попробуйте снова или /menu для отмены.")

    with db() as c:
        u = c.execute("SELECT username, full_name FROM users WHERE user_id=?", (mentor_id,)).fetchone()
        if not u:
            return await send_with_photo(message, "Пользователь с таким ID не найден в базе (он не нажимал /start).")
        m = c.execute("SELECT user_id FROM mentors WHERE user_id=?", (mentor_id,)).fetchone()
        if m:
            return await send_with_photo(message, "Этот пользователь уже является наставником.")
        display_name = u["full_name"] or f"ID {mentor_id}"
        c.execute(
            "INSERT INTO mentors (user_id, username, display_name) VALUES (?, ?, ?)",
            (mentor_id, u["username"], display_name)
        )
    await state.clear()
    await send_with_photo(message, f"Пользователь {display_name} добавлен в наставники!")
    try:
        await bot.send_message(
            mentor_id,
            "Вас назначили наставником!\n\n"
            "Пожалуйста, заполните свой профиль, чтобы воркеры видели, чему вы можете их научить.\n\n"
            "Для этого напишите /mentor_profile"
        )
    except Exception as e:
        logging.error(f"Не удалось уведомить наставника: {e}")

@router.callback_query(F.data == "admin_photo_menu")
async def admin_photo_menu(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in OWNERS:
        return await call.answer("Нет доступа", show_alert=True)
    await state.set_state(Form.admin_upload_photo)
    await send_with_photo(call.message, "Отправьте новую картинку для меню (как фото).\n\nОтмена: /menu")
    await call.answer()

@router.message(Form.admin_upload_photo, F.photo)
async def admin_photo_save(message: Message, state: FSMContext):
    if message.from_user.id not in OWNERS:
        return
    file_id = message.photo[-1].file_id
    set_setting("menu_photo", file_id)
    await state.clear()
    await send_with_photo(message, "Картинка обновлена! Проверьте /menu")

@router.callback_query(F.data == "admin_text_menu")
async def admin_text_menu(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in OWNERS:
        return await call.answer("Нет доступа", show_alert=True)
    await state.set_state(Form.admin_edit_text)
    current = get_setting("menu_text")
    await send_with_photo(call.message, f"Отправьте новый текст меню.\n\nТекущий:\n{current}\n\nОтмена: /menu")
    await call.answer()

@router.message(Form.admin_edit_text, F.text)
async def admin_text_save(message: Message, state: FSMContext):
    if message.from_user.id not in OWNERS:
        return
    set_setting("menu_text", message.text)
    await state.clear()
    await send_with_photo(message, "Текст меню обновлен! Проверьте /menu")

# ---------- НАЧИСЛЕНИЕ ПРОФИТОВ ----------
@router.message(Command("addprofit"))
async def cmd_addprofit(message: Message, command: CommandObject, bot: Bot):
    if message.from_user.id not in OWNERS:
        return await message.answer("Нет доступа.")
    if not command.args:
        return await message.answer("Использование: /addprofit <user_id> <сумма>\nПример: /addprofit 123456789 1.5")
    try:
        args = command.args.split()
        target_id = int(args[0])
        amount = float(args[1])
    except (IndexError, ValueError):
        return await message.answer("Неверный формат. Пример: /addprofit 123456789 1.5")

    with db() as c:
        u = c.execute("SELECT user_id, mentor_id FROM users WHERE user_id=?", (target_id,)).fetchone()
        if not u:
            return await message.answer("Пользователь с таким ID не найден в базе.")
        mentor_id = u["mentor_id"]
        if mentor_id:
            mentor_share = round(amount * 0.10, 4)
            worker_share = round(amount - mentor_share, 4)
            c.execute("UPDATE users SET profits = profits + 1, profit_sum = profit_sum + ? WHERE user_id=?", (worker_share, target_id))
            c.execute("UPDATE users SET profits = profits + 1, profit_sum = profit_sum + ? WHERE user_id=?", (mentor_share, mentor_id))
        else:
            worker_share = amount
            mentor_share = 0
            c.execute("UPDATE users SET profits = profits + 1, profit_sum = profit_sum + ? WHERE user_id=?", (worker_share, target_id))
    
    await message.answer(f"Пользователю {target_id} начислен профит на {worker_share} Gram.")
    
    try:
        msg_worker = f"Вам начислен новый профит!\nСумма: {worker_share} Gram"
        if mentor_id:
            msg_worker += f"\nИз них 10% ({mentor_share} Gram) ушло вашему наставнику."
        msg_worker += "\n\nПроверить баланс: /menu -> Мои профиты"
        await bot.send_message(target_id, msg_worker)
    except Exception:
        pass
        
    if mentor_id:
        try:
            await bot.send_message(mentor_id, f"Вашему подопечному начислен профит!\nВаша доля (10%): +{mentor_share} Gram")
        except Exception:
            pass

# ---------- ЗАГЛУШКИ И НАВИГАЦИЯ ----------
@router.callback_query(F.data == "menu_bots")
async def menu_bots(call: CallbackQuery):
    await send_with_photo(call.message, "Этот раздел находится в разработке.", back_to_menu_kb())
    await call.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await call.message.delete()
    except Exception:
        pass
    await send_main_menu(call.message, call.from_user.id)
    await call.answer()

# ---------- ОБРАБОТКА ЗАЯВОК (ОСНОВНЫХ) ----------
@router.callback_query(F.data.regexp(r"^(ok|no):\d+$"))
async def decide(call: CallbackQuery, bot: Bot):
    if call.from_user.id not in OWNERS:
        return await call.answer("Нет доступа", show_alert=True)

    action, app_id = call.data.split(":")
    app_id = int(app_id)

    with db() as c:
        app = c.execute("SELECT * FROM apps WHERE id=?", (app_id,)).fetchone()
        if not app:
            return await call.answer("Заявка не найдена", show_alert=True)
        if app["status"] != "pending":
            return await call.answer("Уже обработана", show_alert=True)

        status = "approved" if action == "ok" else "rejected"
        c.execute("UPDATE apps SET status=?, decided_by=? WHERE id=?", (status, call.from_user.id, app_id))
        msgs = c.execute("SELECT chat_id, message_id FROM owner_msgs WHERE app_id=?", (app_id,)).fetchall()

    try:
        if status == "approved":
            await bot.send_message(app["user_id"], f"Ваша заявка одобрена!\n\nВступайте: {INVITE_LINK}\n\nОткрыть меню: /menu")
        else:
            await bot.send_message(app["user_id"], "Ваша заявка отклонена.")
    except Exception as e:
        logging.error(f"Не удалось написать пользователю: {e}")

    label = "ОДОБРЕНО" if status == "approved" else "ОТКЛОНЕНО"
    who = call.from_user.full_name
    for m in msgs:
        try:
            await bot.edit_message_text(
                chat_id=m["chat_id"],
                message_id=m["message_id"],
                text=f"Заявка #{app_id}\n\n{app['full_name']}\n{app['username']}\n{app['user_id']}\n\nОткуда узнал: {app['source']}\nВремя на работу: {app['work_time']}\n\n{label} — {who}",
            )
        except Exception:
            pass

    await call.answer("Готово")

async def main():
    init_db()
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
