import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "ТВОЙ_БОТ_ТОКЕН"
API_URL = "https://phishing-detector-0okz.onrender.com/predict"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне текст или ссылку, я проверю её на фишинг.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        response = requests.post(API_URL, json={"url_or_text": user_text})
        result = response.json().get("result", "Ошибка в ответе от сервера.")
        await update.message.reply_text(f"Результат: {result}")
    except Exception as e:
        await update.message.reply_text("Произошла ошибка при проверке. Попробуйте позже.")
        print(f"Ошибка: {e}")

def start_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    start_bot()