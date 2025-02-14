import os
from dotenv import load_dotenv
from loguru import logger

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')


if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Adding handlers
    app.add_handler(CommandHandler("hello", hello))

    logger.info("Bot is running...")
    app.run_polling()