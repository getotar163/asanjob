"""
AI Translator Bot «Asanjob» — Telegram-бот для перевода текста
на ВСЕ языки мира через Google Gemini AI.
Автор: Асанали Мадгалиев, группа РПЗС 25-8
"""

import os
import json
import logging
import httpx
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Gemini через прямой HTTP (без SDK) ───────────────────────────────────
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"

# httpx клиент с правильным SSL (certifi)
_http = httpx.Client(timeout=30.0)


def gemini_request(prompt: str) -> str | None:
    """Отправляет промпт в Gemini и возвращает текст ответа."""
    try:
        resp = _http.post(
            GEMINI_URL,
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.error("Gemini API error: %s", e)
        return None


def gemini_translate(text: str, target_lang: str) -> dict | None:
    """Переводит текст через Gemini API."""
    prompt = (
        f"You are a professional translator. "
        f"Translate the following text to {target_lang}. "
        f"Respond ONLY with a JSON object: "
        f'{{"source_lang": "<detected language name>", "translation": "<translated text>"}}\n\n'
        f"Text to translate:\n{text}"
    )
    raw = gemini_request(prompt)
    if not raw:
        return None
    try:
        # Убираем markdown обёртку
        clean = raw
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
        return json.loads(clean)
    except Exception as e:
        logger.error("Gemini JSON parse error: %s | raw: %s", e, raw)
        return None


def gemini_detect(text: str) -> str:
    """Определяет язык текста через Gemini."""
    prompt = (
        f"Detect the language of this text. "
        f"Respond with ONLY the language code (e.g. ru, en, kk, tr, ar, etc):\n\n{text[:300]}"
    )
    result = gemini_request(prompt)
    if result:
        return result.lower().strip().replace('"', '').replace("'", "")
    return "auto"


# ── Языки ────────────────────────────────────────────────────────────────

ALL_LANGUAGES = {
    "ru": "Русский", "kk": "Қазақша", "en": "English",
    "tr": "Türkçe", "ar": "العربية", "zh": "中文",
    "es": "Español", "de": "Deutsch", "fr": "Français",
    "ja": "日本語", "ko": "한국어", "pt": "Português", "it": "Italiano",
    "hi": "हिन्दी", "uz": "O'zbek", "ky": "Кыргызча", "uk": "Українська",
    "az": "Azərbaycan", "pl": "Polski", "nl": "Nederlands", "sv": "Svenska",
    "cs": "Čeština", "ro": "Română", "hu": "Magyar",
    "th": "ไทย", "vi": "Tiếng Việt", "id": "Indonesia", "ms": "Melayu",
    "fa": "فارسی", "he": "עברית", "bn": "বাংলা", "ta": "தமிழ்",
    "tg": "Тоҷикӣ", "mn": "Монгол", "ka": "ქართული", "hy": "Հայերեն",
    "el": "Ελληνικά", "fi": "Suomi", "da": "Dansk", "no": "Norsk",
    "bg": "Български", "sr": "Српски", "hr": "Hrvatski", "sk": "Slovenčina",
    "lt": "Lietuvių", "lv": "Latviešu", "et": "Eesti",
    "sq": "Shqip", "af": "Afrikaans", "sw": "Kiswahili", "tl": "Filipino",
    "ur": "اردو", "ne": "नेपाली", "si": "සිංහල",
    "my": "မြန်မာ", "am": "አማርኛ",
    "la": "Latina", "eu": "Euskara", "ca": "Català",
    "cy": "Cymraeg", "ga": "Gaeilge", "is": "Íslenska",
    "be": "Беларуская", "sl": "Slovenščina", "bs": "Bosanski",
    "ml": "മലയാളം", "te": "తెలుగు", "kn": "ಕನ್ನಡ",
    "gu": "ગુજરાતી", "mr": "मराठी", "pa": "ਪੰਜਾਬੀ",
    "ps": "پښتو", "ku": "Kurdî",
    "eo": "Esperanto", "mg": "Malagasy",
    "sn": "Shona", "yo": "Yorùbá", "ig": "Igbo", "ha": "Hausa",
    "so": "Soomaali", "zu": "isiZulu", "xh": "isiXhosa",
    "jw": "Jawa", "su": "Sunda", "ceb": "Cebuano",
    "mi": "Māori", "haw": "Hawaiian", "sm": "Samoa",
}

LANG_FLAGS = {
    "ru": "🇷🇺", "kk": "🇰🇿", "en": "🇬🇧", "tr": "🇹🇷", "ar": "🇸🇦",
    "zh": "🇨🇳", "es": "🇪🇸", "de": "🇩🇪", "fr": "🇫🇷",
    "ja": "🇯🇵", "ko": "🇰🇷", "pt": "🇵🇹", "it": "🇮🇹", "hi": "🇮🇳",
    "uz": "🇺🇿", "ky": "🇰🇬", "uk": "🇺🇦", "az": "🇦🇿", "pl": "🇵🇱",
    "nl": "🇳🇱", "sv": "🇸🇪", "cs": "🇨🇿", "ro": "🇷🇴", "hu": "🇭🇺",
    "th": "🇹🇭", "vi": "🇻🇳", "id": "🇮🇩", "ms": "🇲🇾", "fa": "🇮🇷",
    "he": "🇮🇱", "bn": "🇧🇩", "ta": "🇱🇰", "tg": "🇹🇯", "mn": "🇲🇳",
    "ka": "🇬🇪", "hy": "🇦🇲", "el": "🇬🇷", "fi": "🇫🇮", "da": "🇩🇰",
    "no": "🇳🇴", "bg": "🇧🇬", "sr": "🇷🇸", "hr": "🇭🇷", "sk": "🇸🇰",
    "lt": "🇱🇹", "lv": "🇱🇻", "et": "🇪🇪",
    "sq": "🇦🇱", "af": "🇿🇦", "sw": "🇰🇪", "tl": "🇵🇭",
    "ur": "🇵🇰", "ne": "🇳🇵", "be": "🇧🇾", "sl": "🇸🇮", "bs": "🇧🇦",
}

ALL_CODES = list(ALL_LANGUAGES.keys())


def lang_display(code: str) -> str:
    flag = LANG_FLAGS.get(code, "🌐")
    name = ALL_LANGUAGES.get(code, code)
    return f"{flag} {name}"


# ── Пагинация ───────────────────────────────────────────────────────────

PAGE_SIZE = 12


def get_lang_page(page: int, prefix: str = "to") -> InlineKeyboardMarkup:
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    codes = ALL_CODES[start:end]

    rows = []
    for i in range(0, len(codes), 2):
        row = [
            InlineKeyboardButton(lang_display(c), callback_data=f"{prefix}:{c}")
            for c in codes[i:i+2]
        ]
        rows.append(row)

    nav = []
    total_pages = (len(ALL_CODES) + PAGE_SIZE - 1) // PAGE_SIZE
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"page:{prefix}:{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if end < len(ALL_CODES):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"page:{prefix}:{page+1}"))
    rows.append(nav)

    return InlineKeyboardMarkup(rows)


# ── Тексты ───────────────────────────────────────────────────────────────

WELCOME_TEXT = (
    "🌐 <b>AI Translator — Asanjob</b>\n\n"
    "Ассаламуалейкум! ✋\n"
    "Меня зовут <b>Asanjob</b>, я бот-переводчик на базе <b>Google Gemini AI</b> 🤖\n"
    "Автор: <b>Асанали Мадгалиев</b>, группа <b>РПЗС 25-8</b>\n\n"
    "🧠 Я использую <b>искусственный интеллект</b> для перевода!\n"
    "Поддерживаю <b>100+ языков мира</b>.\n\n"
    "Просто отправь текст — я определю язык и переведу.\n\n"
    "📋 <b>Команды:</b>\n"
    "/start — начать\n"
    "/lang — целевой язык\n"
    "/langs — все языки\n"
    "/help — справка\n"
    "/about — обо мне"
)

HELP_TEXT = (
    "📖 <b>Как пользоваться:</b>\n\n"
    "1️⃣ Отправь текст на <b>любом языке</b>\n"
    "2️⃣ Gemini AI определит язык\n"
    "3️⃣ Выбери язык перевода (листай ⬅️➡️)\n\n"
    "💡 Используй /lang — задай язык по умолчанию для мгновенного перевода!\n\n"
    "🧠 Powered by <b>Google Gemini AI</b>"
)

ABOUT_TEXT = (
    "👤 <b>Об авторе:</b>\n\n"
    "🤖 Бот: <b>Asanjob</b> — AI Translator\n"
    "👨‍💻 Автор: <b>Асанали Мадгалиев</b>\n"
    "🎓 Группа: <b>РПЗС 25-8</b>\n"
    "🧠 Движок: <b>Google Gemini AI</b>\n\n"
    "🌍 Переводит на <b>100+ языков мира</b> с помощью ИИ."
)


# ── Обработчики ─────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, parse_mode="HTML")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML")


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ABOUT_TEXT, parse_mode="HTML")


async def cmd_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 <b>Выбери целевой язык:</b>",
        parse_mode="HTML",
        reply_markup=get_lang_page(0, prefix="setlang"),
    )


async def cmd_langs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["🌍 <b>Все языки:</b>\n"]
    for i, code in enumerate(ALL_CODES):
        lines.append(f"  {lang_display(code)}")
        if (i + 1) % 40 == 0 and i + 1 < len(ALL_CODES):
            await update.message.reply_text("\n".join(lines), parse_mode="HTML")
            lines = []
    if lines:
        await update.message.reply_text(
            "\n".join(lines) + f"\n\n<b>Итого: {len(ALL_CODES)} языков</b> 🎉",
            parse_mode="HTML",
        )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "noop":
        return

    if data.startswith("page:"):
        _, prefix, page_str = data.split(":")
        await query.edit_message_reply_markup(
            reply_markup=get_lang_page(int(page_str), prefix=prefix)
        )
        return

    if data.startswith("setlang:"):
        code = data.split(":", 1)[1]
        context.user_data["target_lang"] = code
        await query.edit_message_text(
            f"✅ Целевой язык: <b>{lang_display(code)}</b>\n"
            "Отправляй текст — переведу мгновенно!",
            parse_mode="HTML",
        )
        return

    if data.startswith("to:"):
        target_code = data.split(":", 1)[1]
        original = context.user_data.get("last_text", "")
        if not original:
            return

        target_name = ALL_LANGUAGES.get(target_code, target_code)
        wait_msg = await query.message.reply_text("⏳ Gemini переводит...")

        result = gemini_translate(original, target_name)
        if result and result.get("translation"):
            src = result.get("source_lang", "?")
            await wait_msg.edit_text(
                f"🔍 <b>{src}</b> → <b>{lang_display(target_code)}</b>\n\n"
                f"📝 {result['translation']}",
                parse_mode="HTML",
            )
        else:
            await wait_msg.edit_text("❌ Ошибка. Попробуй ещё раз.")


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if len(text) > 4000:
        await update.message.reply_text("⚠️ Максимум 4000 символов.")
        return

    context.user_data["last_text"] = text

    # Если задан целевой язык — переводим сразу через Gemini
    target_code = context.user_data.get("target_lang")
    if target_code:
        target_name = ALL_LANGUAGES.get(target_code, target_code)
        wait_msg = await update.message.reply_text("⏳ Gemini переводит...")

        result = gemini_translate(text, target_name)
        if result and result.get("translation"):
            src = result.get("source_lang", "?")
            await wait_msg.edit_text(
                f"🔍 <b>{src}</b> → <b>{lang_display(target_code)}</b>\n\n"
                f"📝 {result['translation']}",
                parse_mode="HTML",
            )
        else:
            await wait_msg.edit_text("❌ Ошибка. Попробуй ещё раз.")
        return

    # Иначе — определяем язык и предлагаем выбрать
    detected = gemini_detect(text)
    disp = lang_display(detected) if detected in ALL_LANGUAGES else f"🌐 {detected}"

    await update.message.reply_text(
        f"🔍 Определён язык: <b>{disp}</b>\n\n"
        "🌍 Выбери, на какой язык перевести:",
        parse_mode="HTML",
        reply_markup=get_lang_page(0, prefix="to"),
    )


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN not set!")

    app = (
        ApplicationBuilder()
        .token(token)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .get_updates_connect_timeout(30.0)
        .get_updates_read_timeout(30.0)
        .get_updates_write_timeout(30.0)
        .get_updates_pool_timeout(30.0)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(CommandHandler("lang", cmd_lang))
    app.add_handler(CommandHandler("langs", cmd_langs))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    logger.info("🤖 Asanjob (AI Translator) powered by Gemini — запущен!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
