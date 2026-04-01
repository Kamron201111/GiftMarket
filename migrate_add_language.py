#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Миграция базы данных: добавление поля language
"""

import sqlite3
import os

def migrate_database():
    """Добавить колонку language в таблицу users"""
    
    db_path = 'data/unified.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    print("=" * 80)
    print("🔄 МИГРАЦИЯ БАЗЫ ДАННЫХ")
    print("=" * 80)
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже колонка language
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'language' in columns:
            print("✅ Колонка 'language' уже существует в таблице users")
            print("   Миграция не требуется")
            conn.close()
            return True
        
        print("📝 Добавляем колонку 'language' в таблицу users...")
        
        # Добавляем колонку
        cursor.execute('ALTER TABLE users ADD COLUMN language TEXT DEFAULT "ru"')
        conn.commit()
        
        print("✅ Колонка 'language' успешно добавлена!")
        print()
        
        # Проверяем результат
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("📋 Обновленная структура таблицы users:")
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            default_val = col[4]
            print(f"   • {col_name}: {col_type}" + (f" (default: {default_val})" if default_val else ""))
        
        print()
        
        # Устанавливаем русский язык по умолчанию для всех существующих пользователей
        cursor.execute("UPDATE users SET language = 'ru' WHERE language IS NULL OR language = ''")
        updated_count = cursor.rowcount
        conn.commit()
        
        if updated_count > 0:
            print(f"✅ Установлен русский язык по умолчанию для {updated_count} пользователей")
        
        # Статистика
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE language IS NOT NULL AND language != ''")
        users_with_lang = cursor.fetchone()[0]
        
        print()
        print("📊 Статистика:")
        print(f"   • Всего пользователей: {total_users}")
        print(f"   • Пользователей с языком: {users_with_lang}")
        
        conn.close()
        
        print()
        print("=" * 80)
        print("✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО")
        print("=" * 80)
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        return False

if __name__ == "__main__":
    print()
    success = migrate_database()
    
    if success:
        print("🚀 Теперь можно запускать бота с поддержкой мультиязычности!")
        print()
        print("📝 Следующие шаги:")
        print("   1. Запустите бота: python bot_full_verification.py")
        print("   2. Отправьте /start")
        print("   3. Выберите язык")
        print()
    else:
        print("❌ Миграция не удалась. Проверьте ошибки выше.")
        print()
