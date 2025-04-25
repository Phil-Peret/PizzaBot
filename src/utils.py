from functools import wraps
from telegram import Update
from telegram.ext import (
    CallbackContext,
)
import db
import asyncio


def ensure_is_admin(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if await db.is_admin(update.effective_user.id):
            return await func(update, context, *args, **kwargs)
        else:
            await update.message.reply_text(
                "🚫 Devi essere un admin per eseguire questo comando!"
            )

    return wrapper


def ensure_is_enabled(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if await db.is_enabled(update.effective_user.id):
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
        if await db.is_rider(update.effective_user.id) or await db.is_admin(
            update.effective_user.id
        ):
            return await func(update, context, *args, **kwargs)
        else:
            await update.message.reply_text(
                f"""🚫 Non sei il rider di questa pizzata, attendi la prossima!"""
            )

    return wrapper


async def rider_already_selected() -> bool:
    order = await db.current_order()
    rider = await db.get_current_rider(order["id"])
    return rider is not None


async def notify_admin(message: str, app) -> None:
    admins = await db.all_admin()
    await asyncio.gather(
        *(app.bot.send_message(admin["id"], message) for admin in admins),
        return_exceptions=True,
    )


async def notify_users(message: str, app) -> None:
    users = await db.all_enabled_users()
    await asyncio.gather(
        *(app.bot.send_message(user["id"], message) for user in users),
        return_exceptions=True,
    )


async def notify_user(message: str, telegram_id: int, app) -> None:
    await app.bot.send_message(telegram_id, message)


async def price_check(price: float, update: Update) -> bool:
    if price < 0 or price > 20:
        await update.message.reply_message(f"⚠ Prezzo errato ⚠ ")


async def str_check(desc: str) -> bool:
    if len(desc) > 120:
        await update.message.reply_message(f"⚠ Parametri non validi ⚠ ")
