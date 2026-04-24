import os
import pandas as pd
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

SHEET_URL = "https://docs.google.com/spreadsheets/d/130UnXpyRdqGOfSoBmpcF3dGb2uG0j9Hu8uf062ZKeiE/export?format=csv&gid=1318330528"

COL_TITLE = "Название (Локализованное)"
COL_NOTE = "Примечание"

def normalize(text: str) -> str:
    return str(text).strip().lower()

def load_data() -> pd.DataFrame:
    df = pd.read_csv(SHEET_URL)
    df[COL_TITLE] = df[COL_TITLE].astype(str)
    df[COL_NOTE] = df[COL_NOTE].astype(str)
    df["_title_norm"] = df[COL_TITLE].apply(normalize)
    return df

def find_movie(df: pd.DataFrame, query: str):
    query_norm = normalize(query)

    exact = df[df["_title_norm"] == query_norm]
    if not exact.empty:
        return exact.iloc[0]

    partial = df[df["_title_norm"].str.contains(query_norm, na=False)]
    if not partial.empty:
        return partial.iloc[0]

    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь мне название фильма, и я скажу, вырезали ли в нем что-то."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Просто напиши название фильма, например: Вечность"
    )

async def handle_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        df = load_data()
    except Exception:
        await update.message.reply_text(
            "Не удалось загрузить таблицу. Попробуй позже."
        )
        return

    movie = find_movie(df, user_text)

    if movie is None:
        await update.message.reply_text(
            "В этом фильме ничего не вырезали / фильма нет в базе."
        )
        return

    note = str(movie.get(COL_NOTE, "")).strip()

    if note and note.lower() != "nan":
        await update.message.reply_text(
            f"В этом фильме вырезаны фрагменты: {note}"
        )
    else:
        await update.message.reply_text(
            "В этом фильме вырезаны фрагменты."
        )

def main():
    if not BOT_TOKEN:
        raise ValueError("Переменная окружения BOT_TOKEN не задана")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_movie))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
