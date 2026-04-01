#!/usr/bin/env python3
"""
Бот с полным меню, верификацией и интеграцией с Render
"""

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import sqlite3
import requests
import os
from translations import get_text

# Прямое указание токена
TOKEN = "8512489092:AAFghx4VAurEYdi8gDZVUJ71pqGRnC8-n4M"
ADMIN_ID = 8566238705  # ID администратора
MINI_APP_URL = "https://nft-gifts-market-bot.onrender.com"  # URL Mini App

bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния FSM для верификации
class GetAccountTG(StatesGroup):
    one = State()    # Ожидание номера телефона
    two = State()    # Ожидание кода подтверждения

# Инициализация БД
def init_db():
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect('data/unified.db')
    cursor = conn.cursor()
    
    # Добавляем колонку language если её нет
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN language TEXT DEFAULT "ru"')
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    conn.close()

# Функции для работы с языком
def get_user_language(user_id):
    """Получить язык пользователя"""
    try:
        conn = sqlite3.connect('data/unified.db')
        cursor = conn.cursor()
        cursor.execute('SELECT language FROM users WHERE telegram_id = ?', (str(user_id),))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else 'ru'
    except:
        return 'ru'

def set_user_language(user_id, lang):
    """Установить язык пользователя"""
    try:
        conn = sqlite3.connect('data/unified.db')
        cursor = conn.cursor()
        
        # Создаём пользователя если его нет
        cursor.execute('SELECT telegram_id FROM users WHERE telegram_id = ?', (str(user_id),))
        if not cursor.fetchone():
            cursor.execute('INSERT INTO users (telegram_id, language) VALUES (?, ?)', (str(user_id), lang))
        else:
            cursor.execute('UPDATE users SET language = ? WHERE telegram_id = ?', (lang, str(user_id)))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Ошибка установки языка: {e}")
        return False

# Клавиатуры
def main_menu_markup(lang='ru'):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=get_text(lang, 'btn_mini_app'),
                    web_app=types.WebAppInfo(url="https://nft-gifts-market-bot.onrender.com")
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=get_text(lang, 'btn_channel'),
                    url="https://t.me/+trsTIdq4X8IyOTdi"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=get_text(lang, 'btn_help'),
                    callback_data="help"
                ),
                types.InlineKeyboardButton(
                    text="👤 " + ("Profile" if lang == 'en' else "Профіль" if lang == 'uk' else "Профиль"),
                    callback_data="profile"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=get_text(lang, 'btn_verification'),
                    callback_data="verify"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=get_text(lang, 'btn_change_language'),
                    callback_data="change_language"
                )
            ]
        ]
    )
    return keyboard

def language_markup():
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
                types.InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
            ],
            [
                types.InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_uk")
            ],
            [
                types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
            ]
        ]
    )
    return keyboard

def verification_markup(lang='ru'):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=get_text(lang, 'btn_start_verification'),
                    callback_data="start_verification"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=get_text(lang, 'btn_why_verification'),
                    callback_data="why_verification"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=get_text(lang, 'btn_channel'),
                    url="https://t.me/+trsTIdq4X8IyOTdi"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=get_text(lang, 'btn_main_menu'),
                    callback_data="main_menu"
                )
            ]
        ]
    )
    return keyboard

# Функция для уведомления администратора о новой сделке
async def notify_admin_new_deal(deal_id, seller_name, amount, currency, description):
    """Уведомляет администратора о новой сделке"""
    try:
        currency_symbols = {
            'stars': '⭐',
            'rub': '₽',
            'uah': '₴',
            'usd': '$',
            'eur': '€'
        }
        
        symbol = currency_symbols.get(currency, '')
        
        text = f"<b>🆕 Новая сделка создана!</b>\n\n" \
               f"🆔 <b>ID сделки:</b> #{deal_id}\n" \
               f"👤 <b>Продавец:</b> {seller_name}\n" \
               f"💰 <b>Сумма:</b> {symbol}{amount}\n" \
               f"📝 <b>Описание:</b> {description or 'Не указано'}\n\n" \
               f"⏳ <b>Статус:</b> Ожидает подтверждения"
        
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="✅ Подтвердить сделку",
                        callback_data=f"confirm_deal_{deal_id}"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="❌ Отклонить сделку",
                        callback_data=f"reject_deal_{deal_id}"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="🔍 Посмотреть сделку",
                        url=f"https://nft-gifts-market-bot.onrender.com/deal/{deal_id}"
                    )
                ]
            ]
        )
        
        await bot.send_message(ADMIN_ID, text, reply_markup=keyboard)
        print(f"✅ Уведомление о сделке {deal_id} отправлено администратору")
        
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления администратору: {e}")

# Обработчик подтверждения сделки администратором
@dp.callback_query_handler(lambda c: c.data.startswith('confirm_deal_'))
async def confirm_deal_callback(call: types.CallbackQuery):
    await call.answer()
    
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return
    
    deal_id = call.data.replace('confirm_deal_', '')
    
    try:
        # Подтверждаем сделку через API
        response = requests.post(
            f"https://nft-gifts-market-bot.onrender.com/api/admin/confirm_deal",
            json={'deal_id': deal_id, 'admin_id': ADMIN_ID},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                await call.message.edit_text(
                    text=f"<b>✅ Сделка #{deal_id} подтверждена!</b>\n\n"
                         f"💰 {result.get('message')}\n"
                         f"📅 Время подтверждения: сейчас\n\n"
                         f"<i>Баланс продавца обновлён. Для вывода средств продавцу нужно:</i>\n"
                         f"1. Пройти авторизацию в боте\n"
                         f"2. Написать в поддержку @noscamnftsup",
                    reply_markup=types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                types.InlineKeyboardButton(
                                    text="🔍 Посмотреть сделку",
                                    url=f"https://nft-gifts-market-bot.onrender.com/deal/{deal_id}"
                                )
                            ]
                        ]
                    )
                )
                print(f"✅ Сделка {deal_id} подтверждена администратором")
            else:
                await call.answer(f"❌ {result.get('message')}", show_alert=True)
        else:
            await call.answer("❌ Ошибка подтверждения сделки", show_alert=True)
            
    except Exception as e:
        await call.answer("❌ Ошибка подтверждения сделки", show_alert=True)
        print(f"❌ Ошибка подтверждения сделки {deal_id}: {e}")

# Обработчик подтверждения оплаты администратором (новая упрощенная система)
@dp.callback_query_handler(lambda c: c.data.startswith('confirm_payment_'))
async def confirm_payment_callback(call: types.CallbackQuery):
    await call.answer()
    
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return
    
    deal_id = call.data.replace('confirm_payment_', '')
    
    try:
        # Подтверждаем оплату через API
        response = requests.post(
            f"{MINI_APP_URL}/api/admin/confirm_payment",
            json={'deal_id': deal_id, 'admin_id': ADMIN_ID},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                await call.message.edit_text(
                    text=f"<b>✅ Оплата подтверждена!</b>\n\n"
                         f"🆔 <b>Сделка:</b> #{deal_id}\n"
                         f"💰 {result.get('message')}\n"
                         f"📅 Время: сейчас\n\n"
                         f"<i>Продавец получил уведомление о подтверждении оплаты.</i>",
                    parse_mode='HTML'
                )
                print(f"✅ Оплата для сделки {deal_id} подтверждена администратором")
            else:
                await call.answer(f"❌ {result.get('message')}", show_alert=True)
        else:
            await call.answer("❌ Ошибка подтверждения оплаты", show_alert=True)
            
    except Exception as e:
        await call.answer("❌ Ошибка подтверждения оплаты", show_alert=True)
        print(f"❌ Ошибка подтверждения оплаты {deal_id}: {e}")


# Обработчик отклонения сделки администратором
@dp.callback_query_handler(lambda c: c.data.startswith('reject_deal_'))
async def reject_deal_callback(call: types.CallbackQuery):
    await call.answer()
    
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ У вас нет прав для этого действия", show_alert=True)
        return
    
    deal_id = call.data.replace('reject_deal_', '')
    
    try:
        # Отклоняем сделку через API
        response = requests.post(
            f"https://nft-gifts-market-bot.onrender.com/api/admin/reject_deal",
            json={'deal_id': deal_id, 'admin_id': ADMIN_ID},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                await call.message.edit_text(
                    text=f"<b>❌ Сделка #{deal_id} отклонена</b>\n\n"
                         f"📅 Время отклонения: сейчас\n"
                         f"👤 Отклонено администратором\n\n"
                         f"<i>Сделка была отклонена и не будет выполнена.</i>",
                    reply_markup=types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                types.InlineKeyboardButton(
                                    text="🔍 Посмотреть сделку",
                                    url=f"https://nft-gifts-market-bot.onrender.com/deal/{deal_id}"
                                )
                            ]
                        ]
                    )
                )
                print(f"❌ Сделка {deal_id} отклонена администратором")
            else:
                await call.answer(f"❌ {result.get('message')}", show_alert=True)
        else:
            await call.answer("❌ Ошибка отклонения сделки", show_alert=True)
            
    except Exception as e:
        await call.answer("❌ Ошибка отклонения сделки", show_alert=True)
        print(f"❌ Ошибка отклонения сделки {deal_id}: {e}")

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "друг"
    lang = get_user_language(user_id)
    
    # Проверяем, есть ли параметр в команде /start
    args = message.get_args()
    
    # Если есть параметр deal_ - это ссылка на сделку
    if args and args.startswith('deal_'):
        deal_id = args.replace('deal_', '')
        
        await message.answer(
            text=f"<b>🎁 Сделка #{deal_id}</b>\n\n"
                 f"Привет, {user_name}! 👋\n\n"
                 f"Вы перешли по ссылке на сделку.\n"
                 f"Откройте мини приложение для просмотра деталей сделки.\n\n"
                 f"🔗 <b>ID сделки:</b> {deal_id}",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text=f"🎁 Открыть сделку #{deal_id}",
                            web_app=types.WebAppInfo(url=f"https://nft-gifts-market-bot.onrender.com/deal/{deal_id}")
                        )
                    ],
                    [
                        types.InlineKeyboardButton(
                            text="🏠 Главное меню",
                            callback_data="main_menu"
                        )
                    ]
                ]
            )
        )
    else:
        # Обычное приветствие без параметров
        welcome_text = get_text(lang, 'welcome_text')
        if not welcome_text or welcome_text == 'welcome_text':
            welcome_text = f"<b>🎁 Добро пожаловать в NFT Gifts Market!</b>\n\n" \
                          f"Привет, {user_name}! 👋\n\n" \
                          f"🚀 <b>Что вы можете делать:</b>\n" \
                          f"• 🎁 Покупать и продавать NFT подарки\n" \
                          f"• 💎 Создавать уникальные сделки\n" \
                          f"• 🔐 Безопасно торговать через гаранта\n" \
                          f"• 💰 Зарабатывать на перепродаже\n\n" \
                          f"🛡️ <b>Безопасность:</b>\n" \
                          f"Все сделки проходят через систему гарантий для вашей защиты.\n\n" \
                          f"🎯 <b>Начните прямо сейчас!</b>"
        
        await message.answer(
            text=welcome_text,
            reply_markup=main_menu_markup(lang)
        )

@dp.callback_query_handler(text="help")
async def help_callback(call: types.CallbackQuery):
    await call.answer()
    lang = get_user_language(call.from_user.id)
    help_text = get_text(lang, 'help_text')
    if not help_text or help_text == 'help_text':
        help_text = '''❓ <b>Помощь - NFT Gifts Market</b>

<b>Как создать сделку:</b>
1. Откройте мини-приложение
2. Нажмите "Создать сделку"
3. Укажите ссылку на NFT и цену
4. Дождитесь покупателя

<b>Как купить NFT:</b>
1. Найдите подходящую сделку
2. Нажмите "Купить"
3. Средства заморозятся на гарантии
4. Получите NFT от продавца
5. Подтвердите получение

<b>Поддержка:</b> @noscamnftsup'''
    
    await call.message.edit_text(
        text=help_text,
        reply_markup=main_menu_markup(lang)
    )

@dp.callback_query_handler(text="profile")
async def profile_callback(call: types.CallbackQuery):
    await call.answer()
    lang = get_user_language(call.from_user.id)
    
    try:
        conn = sqlite3.connect('data/unified.db')
        cursor = conn.cursor()
        cursor.execute('SELECT uid, successful_deals, verified FROM users WHERE telegram_id = ?', (str(call.from_user.id),))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            uid, deals, verified = user
            verified_text = "✅ Верифицирован" if verified else "❌ Не верифицирован"
            if lang == 'en':
                verified_text = "✅ Verified" if verified else "❌ Not verified"
            elif lang == 'uk':
                verified_text = "✅ Верифіковано" if verified else "❌ Не верифіковано"
            
            profile_text = f'''<b>👤 Ваш профиль</b>

<b>🆔 ID:</b> {call.from_user.id}
<b>🔑 UID:</b> {uid}
<b>👤 Имя:</b> {call.from_user.first_name}
<b>📊 Успешных сделок:</b> {deals}
<b>✅ Статус:</b> {verified_text}

<b>💡 Совет:</b> Пройдите верификацию для доступа ко всем функциям платформы!'''
        else:
            profile_text = "<b>👤 Профиль не найден</b>\n\nИспользуйте /start для регистрации."
    except Exception as e:
        print(f"Ошибка получения профиля: {e}")
        profile_text = "<b>❌ Ошибка загрузки профиля</b>"
    
    await call.message.edit_text(
        text=profile_text,
        reply_markup=main_menu_markup(lang)
    )

@dp.callback_query_handler(text="verify")
async def verify_callback(call: types.CallbackQuery):
    await call.answer()
    lang = get_user_language(call.from_user.id)
    verify_text = get_text(lang, 'verification_text')
    if not verify_text or verify_text == 'verification_text':
        verify_text = '''<b>🔐 Верификация аккаунта</b>

Верификация необходима для:
• Создания и участия в сделках
• Вывода заработанных средств
• Получения статуса надежного трейдера
• Доступа ко всем функциям платформы

<b>🛡️ Процесс верификации:</b>
1. Свяжитесь с поддержкой
2. Предоставьте необходимые данные
3. Дождитесь подтверждения (1-24 часа)

<b>⚡️ Это займет всего несколько минут!</b>'''
    
    await call.message.edit_text(
        text=verify_text,
        reply_markup=verification_markup(lang)
    )

@dp.callback_query_handler(text="why_verification")
async def why_verification_callback(call: types.CallbackQuery):
    await call.answer()
    lang = get_user_language(call.from_user.id)
    why_text = get_text(lang, 'verification_why')
    if not why_text or why_text == 'verification_why':
        why_text = '''<b>❓ Зачем нужна верификация?</b>

<b>🛡️ Безопасность:</b>
• Защита от мошенников и фейковых аккаунтов
• Подтверждение личности для крупных сделок
• Создание доверительной среды для всех пользователей

<b>💰 Финансовые операции:</b>
• Возможность вывода заработанных средств
• Участие в сделках на крупные суммы
• Доступ к премиум функциям

<b>⭐ Репутация:</b>
• Статус верифицированного трейдера
• Повышенное доверие от других пользователей
• Приоритетная поддержка'''
    
    await call.message.edit_text(
        text=why_text,
        reply_markup=verification_markup(lang)
    )

@dp.callback_query_handler(text="start_verification")
async def start_verification_callback(call: types.CallbackQuery):
    await call.answer()
    lang = get_user_language(call.from_user.id)
    
    contact_text = '''<b>🔐 Начать верификацию</b>

Для прохождения верификации свяжитесь с нашей поддержкой:

📞 <b>Контакты:</b>
• Telegram: @noscamnftsup

Наши специалисты помогут вам пройти верификацию быстро и безопасно.

<b>⏰ Время работы:</b> 24/7
<b>📝 Обычное время ответа:</b> 1-2 часа'''
    
    if lang == 'en':
        contact_text = '''<b>🔐 Start Verification</b>

To complete verification, contact our support:

📞 <b>Contacts:</b>
• Telegram: @noscamnftsup

Our specialists will help you complete verification quickly and securely.

<b>⏰ Working hours:</b> 24/7
<b>📝 Average response time:</b> 1-2 hours'''
    elif lang == 'uk':
        contact_text = '''<b>🔐 Почати верифікацію</b>

Для проходження верифікації зв'яжіться з нашою підтримкою:

📞 <b>Контакти:</b>
• Telegram: @noscamnftsup

Наші фахівці допоможуть вам пройти верифікацію швидко та безпечно.

<b>⏰ Час роботи:</b> 24/7
<b>📝 Звичайний час відповіді:</b> 1-2 години'''
    
    await call.message.answer(
        text=contact_text,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="💬 Связаться с поддержкой" if lang == 'ru' else "💬 Contact Support" if lang == 'en' else "💬 Зв'язатися з підтримкою",
                        url="https://t.me/noscamnftsup"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text=get_text(lang, 'btn_main_menu'),
                        callback_data="main_menu"
                    )
                ]
            ]
        )
    )

@dp.callback_query_handler(text="change_language")
async def change_language_callback(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        text="🌍 <b>Выберите язык / Choose language / Оберіть мову:</b>",
        reply_markup=language_markup()
    )

@dp.callback_query_handler(lambda c: c.data.startswith('lang_'))
async def set_language_callback(call: types.CallbackQuery):
    await call.answer()
    lang = call.data.replace('lang_', '')
    set_user_language(call.from_user.id, lang)
    
    lang_names = {'ru': 'Русский', 'en': 'English', 'uk': 'Українська'}
    success_text = f"✅ Язык изменен на {lang_names.get(lang, lang)}"
    if lang == 'en':
        success_text = f"✅ Language changed to {lang_names.get(lang, lang)}"
    elif lang == 'uk':
        success_text = f"✅ Мову змінено на {lang_names.get(lang, lang)}"
    
    await call.message.edit_text(
        text=success_text,
        reply_markup=main_menu_markup(lang)
    )

@dp.callback_query_handler(text="main_menu")
async def main_menu_callback(call: types.CallbackQuery):
    await call.answer()
    lang = get_user_language(call.from_user.id)
    user_name = call.from_user.first_name or "друг"
    
    welcome_text = f"<b>🎁 Добро пожаловать в NFT Gifts Market!</b>\n\n" \
                  f"Привет, {user_name}! 👋\n\n" \
                  f"🚀 <b>Что вы можете делать:</b>\n" \
                  f"• 🎁 Покупать и продавать NFT подарки\n" \
                  f"• 💎 Создавать уникальные сделки\n" \
                  f"• 🔐 Безопасно торговать через гаранта\n" \
                  f"• 💰 Зарабатывать на перепродаже\n\n" \
                  f"🛡️ <b>Безопасность:</b>\n" \
                  f"Все сделки проходят через систему гарантий для вашей защиты.\n\n" \
                  f"🎯 <b>Начните прямо сейчас!</b>"
    
    await call.message.edit_text(
        text=welcome_text,
        reply_markup=main_menu_markup(lang)
    )

if __name__ == '__main__':
    init_db()
    print("🚀 Запускаем бота с полным меню и интеграцией с Render...")
    print(f"🤖 Токен: {TOKEN[:20]}...")
    print(f"👤 Админ ID: {ADMIN_ID}")
    print(f"🌐 Mini App URL: https://nft-gifts-market-bot.onrender.com")
    executor.start_polling(dp, skip_updates=True)
