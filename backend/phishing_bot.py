from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import requests

API_URL = "https://phishing-detector-0okz.onrender.com/predict"
BOT_TOKEN = "7397260003:AAE9fpOUFf_Y3OYpLq1NHFegBaAP6z_bNOk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Отправь ссылку или текст, и я проверю, фишинг это или нет."
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        res = requests.post(API_URL, json={"url_or_text": user_input})
        result = res.json().get("result")

        if result == "Phishing":
            await update.message.reply_text("⚠️ Это фишинговое сообщение!")
        elif result == "Legitimate":
            await update.message.reply_text("✅ Сообщение безопасное.")
        else:
            await update.message.reply_text("🤔 Не удалось определить.")
    except Exception as e:
        await update.message.reply_text("Ошибка при соединении с API.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check))
    app.run_polling()

if __name__ == "__main__":
    main()