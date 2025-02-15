import os
import pymysql.cursors
from functools import wraps

from dotenv import load_dotenv
from loguru import logger

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext

load_dotenv()


def ensure_is_admin(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if await is_admin(update, context):
            return await func(update, context, *args, **kwargs)
        else:
            await update.message.reply_text("🚫 Devi essere un admin per eseguire questo comando!")
    return wrapper


def get_db_connection():
    return pymysql.connect(host='database',
                             user='root',
                             password=os.getenv('DB_PASSWORD'),
                             database='pizza311bot',
                             cursorclass=pymysql.cursors.DictCursor)


async def is_admin(update: Update, context: CallbackContext) -> bool:
    telegram_id = update.effective_user.id

    # Getting user admins
    connection = get_db_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "SELECT telegram_id FROM users WHERE is_enabled = 1 AND is_admin = 1;"
            cursor.execute(sql)

            admin_ids = [elem['telegram_id'] for elem in cursor.fetchall()]

    return telegram_id in admin_ids


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"""Ciao, io sono il bot del 311 per la pizza!

Tramite questo bot potrai:
  - Richiedere la registrazione al bot
  - Registrarti come "rider" per andare a prendere tu le pizze
  - Prenotare la tua pizza preferita per questa settimana

Quando sei pronto, comincia con il registrarti tramite il comando /registrami !"""
    )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_chat.first_name + ' ' + update.effective_chat.last_name
    telegram_id = update.effective_chat.id

    # Adding user to database in users with authorized = 0 for further authorization
    connection = get_db_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "INSERT INTO users (telegram_id, username) VALUES (%s, %s) ON DUPLICATE KEY UPDATE telegram_id = telegram_id;"
            cursor.execute(sql, (telegram_id, username))

        connection.commit()

    # TODO: Notifying all admins of registration, so that they can accept the new user ASAP

    response = f"""Ciao {username}, sarai tra poco accettato nel bot da un amministratore!

Non appena avremmo conferma, ti verrá notificato qui l'esito della registrazione :)"""

    await update.message.reply_text(response)


@ensure_is_admin
async def list_accept_registrations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Getting list of not-already-enabled users
    connection = get_db_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "SELECT telegram_id, username FROM users WHERE is_enabled = 0;"
            cursor.execute(sql)
            results = cursor.fetchall()

    response = "Lista utenti da accettare:\n\n"
    for result in results:
        response += f"[{result['username']}]\n"
        response += f"/accetta {result['telegram_id']}\n\n"
    else:
        response += "Nessuno, che tristezza!"

    await update.message.reply_text(response)


@ensure_is_admin
async def accept_registration(update: Update, context: ContextTypes) -> None:
    try:
        telegram_id = int(update.message.text.split(' ')[1])

        connection = get_db_connection()
        with connection:
            with connection.cursor() as cursor:
                sql = "UPDATE users SET is_enabled = 1 WHERE telegram_id = %s;"
                cursor.execute(sql, telegram_id)

            connection.commit()

        await update.message.reply_text("Utente abilitato con successo!")
    except Exception as e:
        logger.error(str(e))
        await update.message.reply_text("Utente invalido!")


if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Info handlers
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("start", info))
    app.add_handler(CommandHandler("help", info))

    # User registration handlers
    app.add_handler(CommandHandler("registrami", register))
    app.add_handler(CommandHandler('lista_attesa', list_accept_registrations))
    app.add_handler(CommandHandler('accetta', accept_registration, has_args=1))

    logger.info("Bot is running...")
    app.run_polling()