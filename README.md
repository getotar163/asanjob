# Asanjob — AI Translator Bot 🌐

Telegram-бот для перевода текста на **100+ языков** с помощью **Google Gemini AI**.

**Автор:** Асанали Мадгалиев, группа РПЗС 25-8

## Деплой на Render.com (бесплатно)

### 1. Загрузи на GitHub
```bash
git init
git add .
git commit -m "Asanjob bot"
git remote add origin https://github.com/ТВОЙ_ЮЗЕРНЕЙМ/asanjob-bot.git
git push -u origin main
```

### 2. Зайди на [render.com](https://render.com)
- Зарегистрируйся через GitHub
- Нажми **New → Background Worker**
- Подключи репозиторий `asanjob-bot`
- Runtime: **Python**
- Build Command: `pip install -r requirements.txt`
- Start Command: `python bot.py`

### 3. Добавь переменные окружения
В разделе **Environment** добавь:
- `BOT_TOKEN` = `твой токен бота`
- `GEMINI_API_KEY` = `твой ключ Gemini`

### 4. Нажми Deploy! 🚀

Бот будет работать 24/7 бесплатно.

## Команды бота
- `/start` — Ассаламуалейкум!
- `/lang` — выбрать язык по умолчанию
- `/langs` — все 100+ языков
- `/help` — справка
- `/about` — об авторе
