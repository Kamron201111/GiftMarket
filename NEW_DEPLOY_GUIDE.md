# 🚀 Полная инструкция: Новый репозиторий + Новый Render

## Часть 1: Создание нового GitHub репозитория

### Шаг 1: Создайте репозиторий на GitHub

1. Откройте: https://github.com/new
2. Заполните форму:

```
Repository owner: [ваш username]
Repository name*: nft-gifts-market-bot
Description: NFT Gifts Market - Telegram bot with multilanguage support

Visibility: 
☑ Public (рекомендуется для бесплатного Render)

☑ Add a README file
☐ Add .gitignore (не нужно, создадим сами)
☐ Choose a license (опционально)
```

3. Нажмите **"Create repository"**

### Шаг 2: Подготовьте файлы для загрузки

Из папки `GITHUB_DEPLOY/` нужны следующие файлы:

#### Обязательные файлы:
```
✅ bot_full_verification.py       - Основной бот
✅ translations.py                 - Система переводов
✅ migrate_add_language.py         - Миграция БД
✅ mini_app.py                     - Веб-сервер
✅ db_helpers.py                   - Помощники для БД
```

#### Папки:
```
✅ templates/                      - HTML шаблоны
   └── mini_app/
       ├── base.html
       ├── index.html
       ├── profile.html
       ├── deals.html
       ├── deal.html
       ├── create.html
       ├── link_uid.html
       └── admin.html

✅ static/                         - CSS и статика
   └── style.css

✅ modules/                        - Модули бота
   └── users/
       └── standart.py

✅ markup/                         - Клавиатуры
   └── defaut.py
```

#### Конфигурационные файлы:
```
✅ requirements.txt                - Python зависимости
✅ render.yaml                     - Конфигурация Render
✅ .gitignore                      - Игнорируемые файлы
```

### Шаг 3: Создайте необходимые файлы

#### 3.1. requirements.txt

Создайте файл `requirements.txt`:
```
aiogram==2.25.1
telethon==1.28.5
flask==2.3.0
requests==2.31.0
```

#### 3.2. .gitignore

Создайте файл `.gitignore`:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Database
*.db
*.db-journal
*.db-wal
*.db-shm
data/

# Session files
session/
*.session
*.session-journal

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Environment
.env
config.ini

# Temporary
*.tmp
*.bak
```

#### 3.3. render.yaml

Создайте файл `render.yaml`:
```yaml
services:
  # Web Service (Mini App)
  - type: web
    name: nft-gifts-market-web
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python mini_app.py"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: BOT_TOKEN
        value: 8512489092:AAFghx4VAurEYdi8gDZVUJ71pqGRnC8-n4M
      - key: ADMIN_ID
        value: 8566238705

  # Background Worker (Bot)
  - type: worker
    name: nft-gifts-market-bot
    env: python
    buildCommand: "pip install -r requirements.txt && python migrate_add_language.py"
    startCommand: "python bot_full_verification.py"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: BOT_TOKEN
        value: 8512489092:AAFghx4VAurEYdi8gDZVUJ71pqGRnC8-n4M
      - key: ADMIN_ID
        value: 8566238705
      - key: API_ID
        value: 38295001
      - key: API_HASH
        value: c72727eb4fc2c7f555871e727bf5d942
```

#### 3.4. README.md

Создайте файл `README.md`:
```markdown
# NFT Gifts Market Bot

Telegram bot for safe NFT gifts trading with multilanguage support.

## Features

- 🌍 Multilanguage support (Russian, English, Ukrainian)
- 🎁 NFT gifts marketplace
- 🔐 Verification system
- 💰 Balance management
- 📊 Admin panel
- 🔗 UID linking system

## Languages

- 🇷🇺 Русский
- 🇬🇧 English
- 🇺🇦 Українська

## Tech Stack

- Python 3.11
- aiogram (Telegram Bot API)
- Flask (Web server)
- SQLite (Database)
- Telethon (Telegram Client)

## Deployment

Deployed on Render.com

## Bot

[@noscamnftrbot](https://t.me/noscamnftrbot)
```

### Шаг 4: Загрузите файлы на GitHub

#### Вариант A: Через веб-интерфейс (проще)

1. Откройте ваш новый репозиторий на GitHub
2. Нажмите **"Add file"** → **"Upload files"**
3. Перетащите все файлы и папки из `GITHUB_DEPLOY/`
4. Commit message: `Initial commit with multilanguage support`
5. Нажмите **"Commit changes"**

#### Вариант B: Через Git (для опытных)

```bash
# Клонируйте репозиторий
git clone https://github.com/ваш-username/nft-gifts-market-bot.git
cd nft-gifts-market-bot

# Скопируйте файлы из GITHUB_DEPLOY
copy C:\Users\рома\Desktop\юот\tg\GITHUB_DEPLOY\* .

# Добавьте файлы
git add .

# Commit
git commit -m "Initial commit with multilanguage support"

# Push
git push origin main
```

---

## Часть 2: Создание нового Render веб-сайта

### Шаг 1: Создайте аккаунт на Render (если нет)

1. Откройте: https://render.com
2. Нажмите **"Get Started"**
3. Войдите через GitHub

### Шаг 2: Подключите GitHub репозиторий

1. В Render Dashboard нажмите **"New +"**
2. Выберите **"Blueprint"**
3. Нажмите **"Connect a repository"**
4. Найдите ваш репозиторий: `nft-gifts-market-bot`
5. Нажмите **"Connect"**

### Шаг 3: Настройте сервисы

Render автоматически прочитает `render.yaml` и создаст 2 сервиса:

#### Сервис 1: Web Service (Mini App)
```
Name: nft-gifts-market-web
Type: Web Service
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: python mini_app.py
```

#### Сервис 2: Background Worker (Bot)
```
Name: nft-gifts-market-bot
Type: Background Worker
Environment: Python 3
Build Command: pip install -r requirements.txt && python migrate_add_language.py
Start Command: python bot_full_verification.py
```

### Шаг 4: Дождитесь деплоя

1. Render начнет деплой автоматически
2. Процесс займет 5-10 минут
3. Следите за логами в разделе **"Events"**

### Шаг 5: Получите URL веб-сервиса

1. Откройте сервис **nft-gifts-market-web**
2. Скопируйте URL (например: `https://nft-gifts-market-web.onrender.com`)
3. Этот URL нужно будет использовать в боте

### Шаг 6: Обновите URL в боте

Если URL отличается от `https://nft-gifts-market-uid.onrender.com`:

1. Откройте `bot_full_verification.py` на GitHub
2. Найдите строку:
```python
web_app=types.WebAppInfo(url="https://nft-gifts-market-uid.onrender.com")
```
3. Замените на ваш новый URL
4. Commit и push

---

## Часть 3: Проверка работы

### Шаг 1: Проверьте веб-сервис

1. Откройте URL вашего веб-сервиса в браузере
2. Должна открыться главная страница мини-приложения
3. Проверьте, что нет ошибок

### Шаг 2: Проверьте бота

1. Откройте Telegram
2. Найдите бота: @noscamnftrbot
3. Отправьте `/start`
4. Должен появиться выбор языка:
```
🌍 Choose your language / Выберите язык / Оберіть мову

[🇷🇺 Русский]
[🇬🇧 English]
[🇺🇦 Українська]
```

### Шаг 3: Проверьте мини-приложение

1. В боте нажмите **"🎁 Открыть приложение"**
2. Должно открыться мини-приложение
3. Проверьте все функции

---

## Часть 4: Настройка переменных окружения (опционально)

Если хотите скрыть токены:

### На Render:

1. Откройте каждый сервис
2. Перейдите в **"Environment"**
3. Добавьте переменные:
```
BOT_TOKEN = 8512489092:AAFghx4VAurEYdi8gDZVUJ71pqGRnC8-n4M
ADMIN_ID = 8566238705
API_ID = 38295001
API_HASH = c72727eb4fc2c7f555871e727bf5d942
```

### В коде:

Замените хардкод на переменные окружения:
```python
import os

TOKEN = os.getenv('BOT_TOKEN', '8512489092:AAFghx4VAurEYdi8gDZVUJ71pqGRnC8-n4M')
ADMIN_ID = int(os.getenv('ADMIN_ID', '8566238705'))
API_ID = int(os.getenv('API_ID', '38295001'))
API_HASH = os.getenv('API_HASH', 'c72727eb4fc2c7f555871e727bf5d942')
```

---

## Часть 5: Мониторинг и логи

### Просмотр логов:

1. Render Dashboard → Ваш сервис
2. Вкладка **"Logs"**
3. Смотрите логи в реальном времени

### Проверка статуса:

1. Render Dashboard → Ваш сервис
2. Вкладка **"Events"**
3. Смотрите историю деплоев

---

## 📋 Чек-лист

### GitHub:
- [ ] Создан новый репозиторий
- [ ] Загружены все файлы из GITHUB_DEPLOY
- [ ] Создан requirements.txt
- [ ] Создан .gitignore
- [ ] Создан render.yaml
- [ ] Создан README.md

### Render:
- [ ] Создан аккаунт
- [ ] Подключен GitHub репозиторий
- [ ] Создан Web Service
- [ ] Создан Background Worker
- [ ] Деплой завершен успешно
- [ ] Получен URL веб-сервиса

### Проверка:
- [ ] Веб-сервис открывается в браузере
- [ ] Бот отвечает на /start
- [ ] Показывается выбор языка
- [ ] Мини-приложение открывается
- [ ] Все кнопки работают

---

## 🎉 Готово!

Теперь у вас:
- ✅ Новый GitHub репозиторий
- ✅ Новый Render веб-сайт
- ✅ Работающий бот с мультиязычностью
- ✅ Работающее мини-приложение

**Время выполнения:** 20-30 минут
**Сложность:** Средняя
