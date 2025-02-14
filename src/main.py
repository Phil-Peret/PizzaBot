import os
import pymysql.cursors

from dotenv import load_dotenv
from loguru import logger

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()


def get_db_connection():
    return pymysql.connect(host='database',
                             user='root',
                             password=os.getenv('DB_PASSWORD'),
                             database='pizza311bot',
                             cursorclass=pymysql.cursors.DictCursor)


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def hello_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'{str(get_db_connection())}')


if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Adding handlers
    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(CommandHandler("hello_db", hello_db))

    logger.info("Bot is running...")
    app.run_polling()