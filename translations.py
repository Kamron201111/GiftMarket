#!/usr/bin/env python3
# -*- coding: utf-8 -*-

TRANSLATIONS = {
    'uz': {
        'welcome_text': (
            "🎁 <b>NFT Gifts Market</b> — Telegram NFT sovg'alarini xavfsiz sotib olish va sotish platformasi.\n\n"
            "🛡️ <b>Afzalliklarimiz:</b>\n"
            "• Bitimlar kafolat tizimi\n"
            "• Firibgarlardan himoya\n"
            "• Tez va xavfsiz tranzaksiyalar\n"
            "• 24/7 qo'llab-quvvatlash\n\n"
            "💼 <b>Nima qila olasiz:</b>\n"
            "• NFT sotish bitimlarini yaratish\n"
            "• NFT sovg'alarini xavfsiz sotib olish\n"
            "• Stars orqali to'ldirish\n"
            "• TON hamyon orqali chiqarish\n\n"
            "Amalni tanlang:"
        ),
        'btn_mini_app': "🎁 Ilovani ochish",
        'btn_channel': "📢 Telegram kanalimiz",
        'btn_help': "❓ Yordam",
        'btn_main_menu': "🏠 Asosiy menyu",
        'btn_verification': "✅ Tasdiqlash",
        'verification_menu': "🔐 <b>Akkauntni tasdiqlash</b>",
        'verification_text': (
            "Barcha foydalanuvchilar xavfsizligi uchun tasdiqlash tizimidan foydalanamiz.\n\n"
            "<b>Tasdiqlash beradi:</b>\n"
            "✅ Mablag'larni chiqarish imkoniyati\n"
            "✅ Oshirilgan bitim limiti\n"
            "✅ Tasdiqlangan foydalanuvchi belgisi\n"
            "✅ Ustuvor yordam\n\n"
            "<b>Jarayon:</b>\n"
            "1. \"Tasdiqlashni boshlash\" tugmasini bosing\n"
            "2. Ko'rsatmalarga amal qiling\n"
            "3. Tasdiqlashni kuting (1-24 soat)"
        ),
        'btn_start_verification': "🔐 Tasdiqlashni boshlash",
        'btn_why_verification': "❓ Nima uchun kerak?",
        'verification_why': (
            "❓ <b>Tasdiqlash nima uchun kerak?</b>\n\n"
            "🛡️ Barcha foydalanuvchilarni firibgarlardan himoya qiladi.\n\n"
            "💰 Faqat tasdiqlangan foydalanuvchilar mablag'larini chiqara oladi.\n\n"
            "⭐ Tasdiqlash belgisi ishonchni oshiradi."
        ),
        'help_text': (
            "❓ <b>Yordam — NFT Gifts Market</b>\n\n"
            "<b>Bitim yaratish:</b>\n"
            "1. Ilovani oching\n"
            "2. \"Bitim yaratish\" tugmasini bosing\n"
            "3. NFT havolasi va narxini kiriting\n\n"
            "<b>NFT sotib olish:</b>\n"
            "1. Mos bitimni toping\n"
            "2. \"Sotib olish\" tugmasini bosing\n"
            "3. Mablag'lar kafolatda saqlanadi\n\n"
            "<b>Komissiya:</b> 5%"
        ),
        'support_text': (
            "💬 <b>Yordam markazi</b>\n\n"
            "• Telegram: @noscamnftsup\n"
            "• Ish vaqti: 24/7"
        ),
    }
}

def get_text(lang_code, key, default_lang='uz'):
    lang_code = (lang_code or default_lang).lower()
    if lang_code not in TRANSLATIONS:
        lang_code = default_lang
    return TRANSLATIONS[lang_code].get(key, TRANSLATIONS[default_lang].get(key, key))

def get_user_language(telegram_id, conn):
    cursor = conn.cursor()
    cursor.execute('SELECT language FROM users WHERE telegram_id = ?', (str(telegram_id),))
    result = cursor.fetchone()
    return result[0] if result and result[0] else 'uz'

def set_user_language(telegram_id, language, conn):
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET language = ? WHERE telegram_id = ?', (language, str(telegram_id)))
    conn.commit()
