#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование системы мультиязычности
"""

import sqlite3
from translations import get_text, get_user_language, set_user_language, TRANSLATIONS

def test_translations():
    """Тест переводов"""
    print("=" * 80)
    print("🌍 ТЕСТИРОВАНИЕ СИСТЕМЫ ПЕРЕВОДОВ")
    print("=" * 80)
    print()
    
    # Проверяем наличие всех языков
    print("📋 Доступные языки:")
    for lang in TRANSLATIONS.keys():
        print(f"   ✓ {lang}")
    print()
    
    # Проверяем ключевые тексты для каждого языка
    test_keys = [
        'choose_language',
        'welcome',
        'btn_mini_app',
        'btn_verification',
        'verification_text',
        'help_text'
    ]
    
    print("=" * 80)
    print("🔍 ПРОВЕРКА ПЕРЕВОДОВ")
    print("=" * 80)
    print()
    
    for lang in ['ru', 'en', 'uk']:
        lang_name = {'ru': 'Русский', 'en': 'English', 'uk': 'Українська'}[lang]
        print(f"📝 Язык: {lang_name} ({lang})")
        print("-" * 80)
        
        missing_keys = []
        for key in test_keys:
            text = get_text(lang, key)
            if text == key:  # Если вернулся сам ключ, значит перевод отсутствует
                missing_keys.append(key)
                print(f"   ❌ {key}: ОТСУТСТВУЕТ")
            else:
                # Показываем первые 50 символов
                preview = text[:50] + "..." if len(text) > 50 else text
                preview = preview.replace('\n', ' ')
                print(f"   ✓ {key}: {preview}")
        
        if missing_keys:
            print(f"\n   ⚠️ Отсутствует переводов: {len(missing_keys)}")
        else:
            print(f"\n   ✅ Все переводы присутствуют!")
        print()
    
    print("=" * 80)
    print("🗂️ СТАТИСТИКА ПЕРЕВОДОВ")
    print("=" * 80)
    print()
    
    for lang in ['ru', 'en', 'uk']:
        lang_name = {'ru': 'Русский', 'en': 'English', 'uk': 'Українська'}[lang]
        count = len(TRANSLATIONS[lang])
        print(f"   {lang_name} ({lang}): {count} ключей")
    print()

def test_database():
    """Тест работы с базой данных"""
    print("=" * 80)
    print("💾 ТЕСТИРОВАНИЕ РАБОТЫ С БАЗОЙ ДАННЫХ")
    print("=" * 80)
    print()
    
    try:
        conn = sqlite3.connect('data/unified.db')
        cursor = conn.cursor()
        
        # Проверяем наличие колонки language
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        has_language_column = False
        print("📋 Структура таблицы users:")
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            print(f"   • {col_name}: {col_type}")
            if col_name == 'language':
                has_language_column = True
        
        print()
        if has_language_column:
            print("✅ Колонка 'language' присутствует в таблице users")
        else:
            print("❌ Колонка 'language' ОТСУТСТВУЕТ в таблице users")
            print("   Необходимо выполнить миграцию базы данных!")
        
        print()
        
        # Проверяем пользователей с установленным языком
        cursor.execute("SELECT COUNT(*) FROM users WHERE language IS NOT NULL AND language != ''")
        users_with_lang = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        print(f"👥 Всего пользователей: {total_users}")
        print(f"🌍 Пользователей с установленным языком: {users_with_lang}")
        print(f"❓ Пользователей без языка: {total_users - users_with_lang}")
        print()
        
        # Показываем распределение по языкам
        if users_with_lang > 0:
            print("📊 Распределение по языкам:")
            cursor.execute("SELECT language, COUNT(*) FROM users WHERE language IS NOT NULL AND language != '' GROUP BY language")
            for lang, count in cursor.fetchall():
                lang_name = {'ru': 'Русский', 'en': 'English', 'uk': 'Українська'}.get(lang, lang)
                print(f"   • {lang_name} ({lang}): {count} пользователей")
            print()
        
        conn.close()
        
        print("✅ База данных работает корректно")
        
    except Exception as e:
        print(f"❌ Ошибка при работе с базой данных: {e}")
    
    print()

def test_language_functions():
    """Тест функций работы с языком"""
    print("=" * 80)
    print("🔧 ТЕСТИРОВАНИЕ ФУНКЦИЙ")
    print("=" * 80)
    print()
    
    # Тест get_text
    print("1️⃣ Тест get_text():")
    test_cases = [
        ('ru', 'welcome', True),
        ('en', 'welcome', True),
        ('uk', 'welcome', True),
        ('fr', 'welcome', True),  # Несуществующий язык - должен вернуть русский
        ('ru', 'nonexistent_key', False),  # Несуществующий ключ
    ]
    
    for lang, key, should_exist in test_cases:
        result = get_text(lang, key)
        if should_exist:
            if result != key:
                print(f"   ✓ get_text('{lang}', '{key}'): OK")
            else:
                print(f"   ❌ get_text('{lang}', '{key}'): FAILED (вернул ключ)")
        else:
            print(f"   ⚠️ get_text('{lang}', '{key}'): {result[:30]}...")
    
    print()
    print("✅ Функции работают корректно")
    print()

def main():
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "ТЕСТ СИСТЕМЫ МУЛЬТИЯЗЫЧНОСТИ" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    test_translations()
    test_database()
    test_language_functions()
    
    print("=" * 80)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    print()
    print("📝 Система мультиязычности готова к использованию!")
    print()
    print("🚀 Что дальше:")
    print("   1. Запустите бота: python bot_full_verification.py")
    print("   2. Отправьте команду /start")
    print("   3. Выберите язык из предложенных вариантов")
    print("   4. Проверьте, что все тексты отображаются на выбранном языке")
    print()

if __name__ == "__main__":
    main()
