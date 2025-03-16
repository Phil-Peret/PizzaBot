import asyncio
import os
import pymysql.cursors
import db
from utils import (
    ensure_is_admin,
    ensure_is_enabled,
    ensure_is_rider,
    rider_already_selected,
    notify_admin,
    notify_users,
)
import prettytable as pt
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


@ensure_is_admin
async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    db.delete_user(telegram_id)
    await notify_admin(f"""Utente cancellato: *{telegram_id}*""", app)


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
    username = str(update.effective_chat.username)
    telegram_id = update.effective_chat.id
    # block user already registered
    if db.already_registered(telegram_id):
        await update.message.reply_text(
            f"""Hai già una richiesta in attesa o sei già registrato a questo bot!"""
        )
        return
    # Adding user to database in users with authorized = 0 for further authorization
    await db.add_user_to_register_queue(telegram_id, username)
    await notify_admin(
        f"""Un nuovo utente è in attesa di essere accettato: *{telegram_id}*""", app
    )

    response = f"""Ciao {username}, sarai tra poco accettato nel bot da un amministratore!
Non appena avremmo conferma, ti verrá notificato qui l'esito della registrazione :)"""
    await update.message.reply_text(response)


@ensure_is_admin
async def list_accept_registrations(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    # Getting list of not-already-enabled users
    users = await db.get_unregiter_user()

    table = pt.PrettyTable()
    table.field_names = ["Id", "User"]

    if users:
        for user in users:
            table.add_row(
                [
                    user["id"],
                    user["username"],
                ]
            )
        await update.message.reply_text(
            f"<p>Lista utenti in attesa</p><pre>{table}</pre>", parse_mode="HTML"
        )
    else:
        await update.message.reply_text("Nessun utente da registrare")


@ensure_is_admin
async def accept_registration(update: Update, context: ContextTypes) -> None:
    try:
        telegram_id = int(update.message.text.split(" ")[1])
        db.set_user_enabled(telegram_id)
        await update.message.reply_text("Utente abilitato con successo!")
    except Exception as e:
        logger.error(str(e))
        await update.message.reply_text("Utente non trovato!")


@ensure_is_enabled
async def become_a_rider(update: Update, context: ContextTypes) -> None:
    telegram_id = update.effective_user.id
    if await db.is_rider(telegram_id):
        await update.message.reply_text(f"""Sei giá un rider!""")
    if await rider_already_selected():
        await update.message.reply_text(
            f"""C'è già un rider per questa serata! 
Ordina pure la pizza che prefersici con il comando /ordina"""
        )
        return
    await db.set_rider(telegram_id)
    await update.message.reply_text(
        f"""🛵 Sei diventato rider per questa pizzata!🛵 
Adesso potrai visualizzare la lista delle pizze dei vari utenti e il prezzoper effettuare l'ordine"""
    )


@ensure_is_rider
async def register_rider_description(update: Update, context: ContextTypes) -> None:
    telegram_id = update.effective_user.id
    if not await db.is_rider(telegram_id):
        await update.message.reply_text(f"""Non sei un rider!""")
        return

    new_description = " ".join(update.message.text.split(" ")[1:])
    if len(new_description) == 0:
        await update.message.reply_text(
            f"""Devi per forza avere una descrizione, inseriscila dopo il comando!"""
        )
        return
    await db.update_rider_description(new_description, telegram_id)
    await update.message.reply_text(f"""Descrizione rider aggiornata con successo!""")


@ensure_is_rider
async def check_list_orders(update: Update, context: ContextTypes) -> None:
    order = await db.current_order()
    items = await db.all_item_by_order(order["id"])
    table = pt.PrettyTable()
    table.field_names = ["Id", "username", "Nome", "Prezzo (€)"]

    if items:
        for item in items:
            table.add_row(
                [
                    item["id"],
                    item["username"],
                    item["name"],
                    item["price"],
                ]
            )
        await update.message.reply_text(
            f"<b>🍕 Lista ordini 🍕 </b><pre>{table}</pre>", parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "⚠ *Ancora nessun ordine*⚠ ", parse_mode="MarkdownV2"
        )


@ensure_is_enabled
async def make_personal_order(update: Update, context: CallbackContext) -> None:
    telegram_id = update.effective_user.id
    order = await db.current_order()

    try:
        *name, price = context.args
        name = " ".join(name)
        price = round(float(price), 2)
    except ValueError:
        await update.message.reply_text(
            """⚠ *Comando non riconosciuto* ⚠
Inserisci il nome della pizza e il prezzo nel formato corretto\!
\(es\. `Margherita 5.80`\)\.""",
            parse_mode="MarkdownV2",
        )
        return

    await db.insert_item(name, price, order["id"], telegram_id)
    await update.message.reply_text("""Ordine inserito correttamente.""")


@ensure_is_enabled
async def edit_personal_order(update: Update, context: CallbackContext) -> None:
    telegram_id = update.effective_user.id
    order = await db.current_order()
    try:
        item_id = int(context.args[0])
        name = " ".join(context.args[1:-1])
        price = round(float(context.args[-1]), 2)
    except ValueError:
        await update.message.reply_text(
            """⚠ *Comando non riconosciuto* ⚠
Inserisci id, il nome della pizza e il prezzo nel formato corretto\!
\(es\. `311 Margherita 5.80`\)\.""",
            parse_mode="MarkdownV2",
        )
        return
    except IndexError:
        await update.message.reply_text(
            """Inserisci id, il nome della pizza e il prezzo nel formato corretto\!
\(es\. `311 Margherita 5.80`\)\.""",
            parse_mode="MarkdownV2",
        )
        return
    await db.update_user_item(name, price, order["id"], telegram_id, item_id)
    await update.message.reply_text(
        f"""Ordine {str(item_id)} modificato correttamente!"""
    )


@ensure_is_enabled
async def view_personal_order(update: Update, context: ContextTypes) -> None:
    telegram_id = update.effective_user.id
    order = await db.current_order()
    items = await db.user_items_by_order(telegram_id, order["id"])
    table = pt.PrettyTable()
    table.field_names = ["Id", "Nome", "Prezzo (€)"]

    if items:
        total = float(0)
        for item in items:
            table.add_row([item["id"], item["name"], item["price"]])
            total += float(item["price"])
        table.add_divider()
        table.add_row(["", "TOTALE", f"{total:.2f}"])
        await update.message.reply_text(
            f"<b>🍕 Il tuo ordine 🍕 </b><pre>{table}</pre>", parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "Devi ancora ordinare! Usa il comando /ordina 🍕 "
        )

    # NOTE: Se possibile, oltre a visualizzare il proprio ordine, visualizza anche se lo stato di pagamento da parte del
    # rider che ha ricevuto i soldi é in stato "accettato" e quindi ha confermato che gli sono arrivati i soldi della pizza


@ensure_is_enabled
async def delete_personal_order(update: Update, context: CallbackContext) -> None:
    telegram_id = update.effective_user.id
    order = await db.current_order()
    try:
        if len(context.args) != 1:
            raise ValueError
        item_id = int(context.args[0])
    except ValueError as e:
        await update.message.reply_text(
            "⚠ Comando errato ⚠ \n Inserisci solo l'id dell'ordine da rimuovere"
        )
        return
    await db.delete_user_item(telegram_id, item_id, order["id"])
    await update.message.reply_text("Ordine rimosso")
    # NOTE: Cancella semplicemente l'ordine della pizza; se la pizza é giá stata pagata, notifica il  che deve
    # restituire i soldi all'ordinante MA fregatene di tutto ció che puó avvenire dopo, notifica solo!


@ensure_is_rider
async def confirm_and_close_order(update: Update, context: CallbackContext):
    order = await db.current_order()
    await db.set_order_completated(order["id"])
    await notify_users(
        """L'ordine è stato confermato dal rider, gli ordini sono chiusi!""", app
    )


@ensure_is_enabled
async def view_personal_last_confirmed_order(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    order = await db.last_confirmed_order()
    if not order:
        await update.message.reply_text("Non è stato trovato nessun ordine")
        return
    items = await db.user_items_by_order(telegram_id, order["id"])
    table = pt.PrettyTable()
    table.field_names = ["Id", "Nome", "Prezzo (€)"]
    if items:
        total = float(0)
        for item in items:
            table.add_row([item["id"], item["name"], item["price"]])
            total += float(item["price"])
        table.add_divider()
        table.add_row(["", "TOTALE", f"{total:.2f}"])
        await update.message.reply_text(
            f"<b>🍕 Il tuo ultimo ordine 🍕</b><pre>{table}</pre>", parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "Non hai effettuato un ordine nell'utima pizzata"
        )


@ensure_is_rider
async def view_total_user(update: Update, context: CallbackContext):
    order = await db.last_confirmed_order()
    if not order:
        await update.message.reply_text("Nessun ordine recente confermato")
        return
    total_users = await db.total_order_for_each_user(order["id"])
    table = pt.PrettyTable()
    table.field_names = ["Username", "Prezzo (€)"]
    if total_users:
        total = float(0)
        for total_user in total_users:
            table.add_row([total_user["username"], total_user["total"]])
            total += float(total_user["total"])
        table.add_divider()
        table.add_row(["TOTALE", f"{total:.2f}"])
        await update.message.reply_text(
            f"<b>🍕 Totali per utente 🍕</b><pre>{table}</pre>", parse_mode="HTML"
        )
    else:
        await update.message.reply_text("Non ci sono stati ordini nell'ultima pizzata")


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
        BotCommand("ordine_confermato", "Visualizza l'ultimo ordine confermato"),
    }
    rider_commands = {
        BotCommand("visualizza_ordini", "Visualizza la lista degli ordini"),
        BotCommand(
            "aggiorna_descrizione_rider", "Aggiorna la descrizione pagamento rider"
        ),
        BotCommand("visualizza_totali", "Visualizza i totali per ogni utente"),
        BotCommand("chiudi_ordinazioni", "Chiudi le ordinazioni per questa pizzata"),
    }
    admin_commands = {
        BotCommand("lista_ordini", "Visualizza la lista degli ordini"),
        BotCommand("accetta", "Accetta un utente in attesa"),
        BotCommand("lista_attesa", "Visualizza la lista di attesa utenti"),
        BotCommand("visualizza_totali", "Visualizza i totali per ogni utente"),
        BotCommand("chiudi_ordinazioni", "Chiudi le ordinazioni per questa pizzata"),
    }

    commands = set()
    if await db.already_registered(telegram_id):
        commands.update(registered_commands)
    if await db.is_rider(telegram_id):
        commands.update(rider_commands)
    if await db.is_admin(telegram_id):
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
    app.add_handler(CommandHandler("visualizza_ordini", check_list_orders))
    app.add_handler(
        CommandHandler("aggiorna_descrizione_rider", register_rider_description)
    )
    app.add_handler(
        CommandHandler("ordine_confermato", view_personal_last_confirmed_order)
    )
    app.add_handler(CommandHandler("visualizza_totali", view_total_user))
    app.add_handler(CommandHandler("chiudi_ordinazioni", confirm_and_close_order))
    # Order handlers
    app.add_handler(CommandHandler("ordina", make_personal_order))
    app.add_handler(CommandHandler("modifica_ordine", edit_personal_order))
    app.add_handler(CommandHandler("visualizza_ordine", view_personal_order))
    app.add_handler(CommandHandler("cancella_ordine", delete_personal_order))

    logger.info("Bot is running...")
    app.run_polling()
