import asyncio
import os
import pymysql.cursors
from functools import wraps

from dotenv import load_dotenv
from loguru import logger

from telegram import BotCommand, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    ContextTypes,
)

load_dotenv()


def ensure_is_admin(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if await is_admin(update, context):
            return await func(update, context, *args, **kwargs)
        else:
            await update.message.reply_text(
                "🚫 Devi essere un admin per eseguire questo comando!"
            )

    return wrapper


def ensure_is_enabled(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if await is_enabled(update, context):
            return await func(update, context, *args, **kwargs)
        else:
            await update.message.reply_text(
                f"""🚫 Devi richiedere l'accesso e attendere che un admin ti accetti per eseguire questo comando!
Premi /registrami se ancora non l'hai fatto!"""
            )

    return wrapper


# admin bypass rider check
def ensure_is_rider(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if await (is_rider(update, context) or is_admin(update, context)):
            return await func(update, context, *args, **kwargs)
        else:
            await update.message.reply_text(f"""🚫 Non sei un rider!""")

    return wrapper


def todo_command_not_implemented(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        return await update.message.reply_text(f"""TODO: Funzione da implementare""")

    return wrapper


def get_db_connection():
    return pymysql.connect(
        host="database",
        user="root",
        password=os.getenv("DB_PASSWORD"),
        database="pizza311bot",
        cursorclass=pymysql.cursors.DictCursor,
    )


def is_query_result_true(sql: str, telegram_id: int) -> bool:
    connection = get_db_connection()
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (telegram_id,))
            return cursor.fetchone() is not None


async def is_admin(update: Update, context: CallbackContext) -> bool:
    sql = "SELECT 1 FROM users WHERE telegram_id = %s AND is_enabled = 1 AND is_admin = 1;"
    return is_query_result_true(sql, update.effective_user.id)


async def is_enabled(update: Update, context: CallbackContext) -> bool:
    sql = "SELECT telegram_id FROM users WHERE telegram_id = %s AND is_enabled = 1"
    return is_query_result_true(sql, update.effective_user.id)


async def is_rider(update: Update, context: CallbackContext) -> bool:
    sql = "SELECT 1 FROM riders WHERE telegram_id = %s"
    return is_query_result_true(sql, update.effective_user.id)


async def already_registered(telegram_id: int) -> bool:
    sql = "SELECT 1 FROM users WHERE telegram_id = %s"
    return is_query_result_true(sql, telegram_id)


async def already_rider_selected() -> bool:
    raise NotImplementedError()


@ensure_is_enabled
async def change_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """TODO: modifica o annulla l'ordine di un utente, controllando che il rider non abbia gia' ordinato"""
    raise NotImplementedError()


@ensure_is_admin
async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """TODO: - decidere se cancellare dal db o semplicemente settare flag a non registrato, chiedere prima conferma"""
    username = update.effective_chat.first_name + " " + update.effective_chat.last_name
    connection = get_db_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "DELETE FROM users WHERE telegram_id = %s;"
            cursor.execute(sql, (update.effective_chat.id,))
        connection.commit()
    notify_admin(f"""Utente cancellato: *{username}*""")


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"""Ciao, io sono il bot del 311 per la pizza!

Tramite questo bot potrai:
  - 📋 Richiedere la registrazione al bot
  - 🛵 Registrarti come "rider" per andare a prendere tu le pizze
  - 🍕 Prenotare la tua pizza preferita per questa settimana

Quando sei pronto, comincia con il registrarti tramite il comando /registrami !"""
    )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_chat.first_name + " " + update.effective_chat.last_name
    telegram_id = update.effective_chat.id
    # block user already registered
    if await already_registered(telegram_id):
        await update.message.reply_text(
            f"""Hai già una richiesta in attesa o sei già registrato a questo bot!"""
        )
        return
    # Adding user to database in users with authorized = 0 for further authorization
    connection = get_db_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "INSERT INTO users (telegram_id, username) VALUES (%s, %s) ON DUPLICATE KEY UPDATE telegram_id = telegram_id;"
            cursor.execute(
                sql,
                (
                    telegram_id,
                    username,
                ),
            )
        connection.commit()
    notify_admin(f"""Un nuovo utente è in attesa di essere accettato: *{username}*""")

    response = f"""Ciao {username}, sarai tra poco accettato nel bot da un amministratore!
Non appena avremmo conferma, ti verrá notificato qui l'esito della registrazione :)"""
    await update.message.reply_text(response)


async def notify_admin(message: str) -> None:
    admin_ids = []
    connection = get_db_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "SELECT telegram_id FROM users WHERE is_admin = 1"
            cursor.execute(sql)
            admin_ids = [row["telegram_id"] for row in cursor.fetchall()]
    await asyncio.gather(
        *(app.bot.send_message(admin_id, message) for admin_id in admin_ids)
    )


@ensure_is_admin
async def list_accept_registrations(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    # Getting list of not-already-enabled users
    connection = get_db_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "SELECT telegram_id, username FROM users WHERE is_enabled = 0;"
            cursor.execute(sql)
            results = cursor.fetchall()

    response = "Lista utenti da accettare:\n\n"
    if len(results):
        for result in results:
            response += f"[{result['username']}]\n"
            response += f"/accetta {result['telegram_id']}\n\n"
    else:
        response += "Nessuno, che tristezza!"

    await update.message.reply_text(response)


@ensure_is_admin
async def accept_registration(update: Update, context: ContextTypes) -> None:
    try:
        telegram_id = int(update.message.text.split(" ")[1])

        connection = get_db_connection()
        with connection:
            with connection.cursor() as cursor:
                sql = "UPDATE users SET is_enabled = 1 WHERE telegram_id = %s;"
                cursor.execute(sql, (telegram_id,))

            connection.commit()

        await update.message.reply_text("Utente abilitato con successo!")
    except Exception as e:
        logger.error(str(e))
        await update.message.reply_text("Utente invalido!")


@ensure_is_enabled
async def become_a_rider(update: Update, context: ContextTypes) -> None:
    telegram_id = update.effective_user.id
    if await is_rider(update, context):
        await update.message.reply_text(f"""Sei giá un rider!""")
        return

    connection = get_db_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "INSERT INTO riders (telegram_id, rider_description) VALUES (%s, 'Per pagamenti: scrivere in privato')"
            cursor.execute(sql, (telegram_id,))
        connection.commit()

    await update.message.reply_text(
        f"""Sei diventato rider per le pizzate del 311, grande!"""
    )


@ensure_is_rider
async def register_rider_description(update: Update, context: ContextTypes) -> None:
    telegram_id = update.effective_user.id
    if not await is_rider(update, context):
        await update.message.reply_text(f"""Non sei un rider!""")
        return

    new_description = " ".join(update.message.text.split(" ")[1:])
    if len(new_description) == 0:
        await update.message.reply_text(
            f"""Devi per forza avere una descrizione, inseriscila dopo il comando!"""
        )
        return

    connection = get_db_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "UPDATE riders SET rider_description = %s WHERE telegram_id = %s;"
            cursor.execute(
                sql,
                (
                    new_description,
                    telegram_id,
                ),
            )
        connection.commit()

    await update.message.reply_text(f"""Descrizione rider aggiornata con successo!""")


@ensure_is_rider
@todo_command_not_implemented
async def check_list_orders() -> None:
    """TODO: Ricavare la lista degli ordini e visualizzare il totale provvisorio/definitivo al momento della chiusura delle prenotazioni"""


@todo_command_not_implemented
@ensure_is_enabled
async def make_personal_order():
    """TODO: Implementa funzione di inserimento ordine personale"""

    # NOTE: Ognuno inserisce la sua pizza; una persona NON puó ordinare per gli altri
    # Se hai giá una pizza ordinata, visualizzala in modo che possa decidere se modificare l'ordine o meno


@todo_command_not_implemented
@ensure_is_enabled
async def edit_personal_order():
    """TODO: Implementa funzione di modifica ordine personale"""


@ensure_is_enabled
async def view_personal_order(update: Update, context: ContextTypes) -> None:
    telegram_id = update.effective_user.id
    connection = get_db_connection()
    items = []
    try:
        with connection:
            with connection.cursor() as cursor:
                sql = """SELECT name, price FROM items AS i
                INNER JOIN orders AS o ON o.order_id = i.order_id
                WHERE o.completed = 1 AND 
                i.ordered_by = %s"""
            cursor.execute(sql, (telegram_id,))
            items = [
                {"name": row["name"], "price": row["price"]}
                for row in cursor.fetchall()
            ]

    except Exception as e:
        logger.error(str(e))

    if items:
        response = ""
        for item in items:
            response += item["name"] + " " + item["price"] + "\n"
        await update.message.reply_text(str(response))
    else:
        await update.message.reply_text(
            "Devi ancora ordinare! Usa il comando /ordina 🍕 "
        )

    # NOTE: Se possibile, oltre a visualizzare il proprio ordine, visualizza anche se lo stato di pagamento da parte del
    # rider che ha ricevuto i soldi é in stato "accettato" e quindi ha confermato che gli sono arrivati i soldi della pizza


@todo_command_not_implemented
@ensure_is_enabled
async def delete_personal_order():
    """TODO: Implementa funzione di cancellazione ordine personale"""

    # NOTE: Cancella semplicemente l'ordine della pizza; se la pizza é giá stata pagata, notifica il rider che deve
    # restituire i soldi all'ordinante MA fregatene di tutto ció che puó avvenire dopo, notifica solo!


async def init_user(update: Update, context: ContextTypes) -> None:
    telegram_id = update.effective_user.id

    unregistered_commands = {
        BotCommand("info", "Ricevi informazioni sul bot"),
        BotCommand("start", "Fai partire il bot"),
        BotCommand("registrami", "Registrati al bot"),
    }
    registered_commands = {
        BotCommand("ordina", "Ordina la tua pizza!"),
        BotCommand("modifica_ordine", "Modifica ordine"),
        BotCommand("visualizza_ordine", "Visualizza il tuo ordine"),
        BotCommand("cancella_ordine", "Cancella il tuo ordine"),
        BotCommand("diventa_rider", "Proponiti come rider di questa pizzata!"),
    }
    rider_commands = {
        BotCommand("lista_ordini", "Visualizza la lista degli ordini"),
        BotCommand(
            "aggiorna_descrizione_rider", "Aggiorna la descrizione pagamento rider"
        ),
    }
    admin_commands = {
        BotCommand("lista_ordini", "Visualizza la lista degli ordini"),
        BotCommand("accetta", "Accetta un utente in attesa"),
        BotCommand("lista_attesa", "Visualizza la lista di attesa utenti"),
    }

    commands = set()
    if await already_registered(telegram_id):
        commands.update(registered_commands)
        await update.message.reply_text("""Bentornato brosky!""")
    if await is_rider(update, context):
        commands.update(rider_commands)
        await update.message.reply_text("""Pronto ad andare a prendere altre pizze?""")
    if await is_admin(update, context):
        commands.update(admin_commands)
        await update.message.reply_text(
            """Per controllare la l# Inserisci solo se non ha giá un ordine (fregatene di una persona che ordina per piú persone, ognuno si ordina la sua)ista accettazioni, usa /lista_attesa"""
        )
    else:
        commands = unregistered_commands
        await update.message.reply_text(
            """Non sei ancora registrato, usa il comando /registrami per richiedere l'accesso!"""
        )
    # telegram not accept duplicate commands
    await app.bot.setMyCommands(list(commands))


if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    # Info handlers
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("start", init_user))
    app.add_handler(CommandHandler("help", info))

    # User registration handlers
    app.add_handler(CommandHandler("registrami", register))
    app.add_handler(CommandHandler("lista_attesa", list_accept_registrations))
    app.add_handler(CommandHandler("accetta", accept_registration, has_args=1))
    app.add_handler(CommandHandler("diventa_rider", become_a_rider))
    app.add_handler(CommandHandler("lista_ordini", check_list_orders))
    app.add_handler(
        CommandHandler("aggiorna_descrizione_rider", register_rider_description)
    )

    # Order handlers
    app.add_handler(CommandHandler("ordina", make_personal_order))
    app.add_handler(CommandHandler("modifica_ordine", edit_personal_order))
    app.add_handler(CommandHandler("visualizza_ordine", view_personal_order))
    app.add_handler(CommandHandler("cancella_ordine", delete_personal_order))

    logger.info("Bot is running...")
    app.run_polling()
