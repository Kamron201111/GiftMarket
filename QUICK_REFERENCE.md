# ⚡ Быстрая памятка

## 📁 3 файла для загрузки

Из папки `GITHUB_DEPLOY/`:
1. `bot_full_verification.py`
2. `translations.py` ← НОВЫЙ
3. `migrate_add_language.py` ← НОВЫЙ

## 🚀 3 действия на Render

1. **Дождаться деплоя** (автоматически после push)
2. **Открыть Shell** (Render → Ваш бот → Shell)
3. **Выполнить:** `python migrate_add_language.py`

## ✅ Проверка

Telegram → @noscamnftrbot → `/start` → Выбор языка

---

## 📝 Команды

### GitHub:
```bash
git add bot_full_verification.py translations.py migrate_add_language.py
git commit -m "Add multilanguage support"
git push origin main
```

### Render Shell:
```bash
python migrate_add_language.py
```

---

## 🔗 Ссылки в файлах

Уже правильно настроены:
- `https://nft-gifts-market-uid.onrender.com` ✅

---

**Подробные инструкции:**
- `STEP_BY_STEP.md` - пошаговая
- `VISUAL_GUIDE.md` - визуальная
- `DEPLOY_MULTILANGUAGE.md` - полная
