# 📁 Список файлов для загрузки на GitHub

## ✅ Обязательные файлы (из GITHUB_DEPLOY/)

### Python файлы:
```
bot_full_verification.py       - Основной бот с мультиязычностью
translations.py                - Система переводов (НОВЫЙ)
migrate_add_language.py        - Миграция БД (НОВЫЙ)
mini_app.py                    - Веб-сервер Flask
db_helpers.py                  - Помощники для работы с БД
```

### Папка templates/:
```
templates/mini_app/base.html       - Базовый шаблон
templates/mini_app/index.html      - Главная страница
templates/mini_app/profile.html    - Профиль пользователя
templates/mini_app/deals.html      - Список сделок
templates/mini_app/deal.html       - Страница сделки
templates/mini_app/create.html     - Создание сделки
templates/mini_app/link_uid.html   - Привязка UID
templates/mini_app/admin.html      - Админ панель
```

### Папка static/:
```
static/style.css               - Стили CSS
```

### Папка modules/:
```
modules/users/standart.py      - Модуль пользователей
```

### Папка markup/:
```
markup/defaut.py               - Клавиатуры бота
```

---

## 📝 Файлы для создания вручную

### requirements.txt
```txt
aiogram==2.25.1
telethon==1.28.5
flask==2.3.0
requests==2.31.0
```

### .gitignore
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

### render.yaml
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

  # Background Worker (Bot)
  - type: worker
    name: nft-gifts-market-bot
    env: python
    buildCommand: "pip install -r requirements.txt && python migrate_add_language.py"
    startCommand: "python bot_full_verification.py"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

### README.md
```markdown
# NFT Gifts Market Bot

Telegram bot for safe NFT gifts trading with multilanguage support.

## Features

- 🌍 Multilanguage support (Russian, English, Ukrainian)
- 🎁 NFT gifts marketplace
- 🔐 Verification system
- 💰 Balance management
- 📊 Admin panel

## Languages

- 🇷🇺 Русский
- 🇬🇧 English
- 🇺🇦 Українська

## Bot

[@noscamnftrbot](https://t.me/noscamnftrbot)
```

---

## 📂 Структура репозитория

```
nft-gifts-market-bot/
│
├── bot_full_verification.py
├── translations.py
├── migrate_add_language.py
├── mini_app.py
├── db_helpers.py
│
├── templates/
│   └── mini_app/
│       ├── base.html
│       ├── index.html
│       ├── profile.html
│       ├── deals.html
│       ├── deal.html
│       ├── create.html
│       ├── link_uid.html
│       └── admin.html
│
├── static/
│   └── style.css
│
├── modules/
│   └── users/
│       └── standart.py
│
├── markup/
│   └── defaut.py
│
├── requirements.txt
├── .gitignore
├── render.yaml
└── README.md
```

---

## ⚠️ Файлы НЕ загружать

```
❌ data/                    - База данных (создается автоматически)
❌ session/                 - Сессии (создаются автоматически)
❌ __pycache__/             - Python кеш
❌ *.db                     - Файлы базы данных
❌ *.session                - Файлы сессий
❌ .env                     - Переменные окружения
❌ config.ini               - Конфигурация
```

---

## 🚀 Порядок загрузки

### 1. Создайте репозиторий на GitHub
- Repository name: `nft-gifts-market-bot`
- Public
- Add README

### 2. Загрузите файлы
Через веб-интерфейс GitHub:
- Add file → Upload files
- Перетащите все файлы из GITHUB_DEPLOY/
- Создайте вручную: requirements.txt, .gitignore, render.yaml

### 3. Commit
- Message: "Initial commit with multilanguage support"
- Commit changes

---

## ✅ Проверка

После загрузки на GitHub должны быть:
- [ ] 5 Python файлов в корне
- [ ] Папка templates/ с 8 HTML файлами
- [ ] Папка static/ с style.css
- [ ] Папка modules/users/ с standart.py
- [ ] Папка markup/ с defaut.py
- [ ] requirements.txt
- [ ] .gitignore
- [ ] render.yaml
- [ ] README.md

**Всего:** ~20 файлов

---

**Следующий шаг:** NEW_DEPLOY_GUIDE.md (Часть 2: Создание Render)
