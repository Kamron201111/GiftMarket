#!/usr/bin/env python3
"""
Инициализация базы данных
"""

import sqlite3
import os

def init_database():
    """Создает базу данных с таблицами"""
    try:
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect('data/unified.db')
        cursor = conn.cursor()
        
        # Создаем таблицу пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                balance_stars INTEGER DEFAULT 0,
                balance_rub REAL DEFAULT 0,
                successful_deals INTEGER DEFAULT 0,
                verified BOOLEAN DEFAULT FALSE,
                language TEXT DEFAULT 'ru',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем таблицу сделок
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id TEXT PRIMARY KEY,
                seller_id TEXT NOT NULL,
                nft_link TEXT,
                nft_username TEXT,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ База данных инициализирована успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Инициализация базы данных...")
    init_database()
