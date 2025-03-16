import os
import pymysql.cursors
from loguru import logger
from typing import TypedDict


class item(TypedDict):
    id: int
    telegram_id: int
    username: str
    name: str
    price: float


class order(TypedDict):
    id: int


class user(TypedDict):
    id: int
    username: str


class total(TypedDict):
    username: str
    total: float


def db_connection():
    return pymysql.connect(
        host="database",
        user="root",
        password=os.getenv("DB_PASSWORD"),
        database="pizza311bot",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=10,
    )


async def insert_item(name: str, price: float, order_id: int, telegram_id: int) -> None:
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """INSERT INTO items (order_id, telegram_id, name, price) 
            VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql, (order_id, telegram_id, name, price))
        connection.commit()
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()


async def user_items_by_order(telegram_id: int, order_id: int) -> list[item]:
    user_items = []
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """SELECT items.id, items.name, items.price FROM items
            INNER JOIN orders ON orders.id = items.order_id
            WHERE orders.id = %s AND 
            items.telegram_id = %s;"""
            cursor.execute(
                sql,
                (
                    order_id,
                    telegram_id,
                ),
            )
            rows = cursor.fetchall()
        user_items = [
            {
                "id": row["id"],
                "name": row["name"],
                "price": row["price"],
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()
    return user_items


async def update_user_item(
    name: str, price: str, order_id: int, telegram_id: int, item_id: int
) -> None:
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """UPDATE items 
            SET name = %s, price = %s
            WHERE order_id = %s AND
            telegram_id = %s AND
            id = %s"""
            cursor.execute(sql, (name, price, order_id, telegram_id, item_id))
        connection.commit()
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()


async def all_item_by_order(order_id: int) -> list[item]:
    items = []
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """SELECT items.id, users.id AS telegram_id, users.username, items.name, items.price FROM users
            INNER JOIN items ON items.telegram_id = users.id 
            LEFT JOIN orders ON orders.id = items.order_id
            WHERE orders.id = %s
            ORDER BY users.username"""
            cursor.execute(sql, (order_id,))
            items = [
                {
                    "id": row["id"],
                    "telegram_id": row["telegram_id"],
                    "username": row["username"],
                    "name": row["name"],
                    "price": row["price"],
                }
                for row in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()
    return items


async def current_order() -> order:
    order = None
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """SELECT id FROM orders 
            WHERE completed = 0
            AND event_date >= NOW()
            ORDER BY id ASC
            """
            cursor.execute(sql)
            order = {"id": cursor.fetchone()["id"]}
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()
    return order


async def is_admin(telegram_id: int) -> bool:
    conncetion = db_connection()
    try:
        with conncetion.cursor() as cursor:
            sql = (
                "SELECT 1 FROM users WHERE id = %s AND is_enabled = 1 AND is_admin = 1;"
            )
            cursor.execute(sql, (telegram_id,))
            is_admin = cursor.fetchone() is not None
    except Exception as e:
        logger.error(str(e))
    finally:
        conncetion.close()
    return is_admin


async def is_enabled(telegram_id: int) -> bool:
    conncetion = db_connection()
    try:
        with conncetion.cursor() as cursor:
            sql = "SELECT id FROM users WHERE id = %s AND is_enabled = 1;"
            cursor.execute(sql, (telegram_id,))
            is_enabled = cursor.fetchone() is not None
    except Exception as e:
        logger.error(str(e))
    finally:
        conncetion.close()
    return is_enabled


async def is_rider(telegram_id: int) -> bool:
    conncetion = db_connection()
    try:
        with conncetion.cursor() as cursor:
            sql = "SELECT 1 FROM riders WHERE telegram_id = %s;"
            cursor.execute(sql, (telegram_id,))
            is_rider = cursor.fetchone() is not None
    except Exception as e:
        logger.error(str(e))
    finally:
        conncetion.close()
    return is_rider


async def already_registered(telegram_id: int) -> bool:
    conncetion = db_connection()
    try:
        with conncetion.cursor() as cursor:
            sql = "SELECT 1 FROM users WHERE id = %s"
            cursor.execute(sql, (telegram_id,))
            already_registered = cursor.fetchone() is not None
    except Exception as e:
        logger.error(str(e))
    finally:
        conncetion.close()
    return already_registered


async def update_rider_description(description: str, telegram_id: int) -> None:
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE riders SET rider_description = %s WHERE telegram_id = %s;"
            cursor.execute(
                sql,
                (
                    description,
                    telegram_id,
                ),
            )
        connection.commit()
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()


async def set_rider(telegram_id: int) -> None:
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO riders (telegram_id, rider_description) VALUES (%s, 'Per pagamenti: scrivere in privato')"
            cursor.execute(sql, (telegram_id,))
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()


async def set_user_enabled(telegram_id: int) -> None:
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE users SET is_enabled = 1 WHERE id = %s;"
            cursor.execute(sql, (telegram_id,))
        connection.commit()
    except Exception as e:
        logger.error(str(e))
        raise e
    finally:
        connection.close()


async def get_unregiter_user() -> list[user]:
    users = []
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT id, username FROM users WHERE is_enabled = 0;"
            cursor.execute(sql)
            users = [
                {"id": user["id"], "username": user["username"]}
                for user in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()
    return users


async def all_admin() -> list[user]:
    users = []
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT id FROM users WHERE is_admin = 1"
            cursor.execute(sql)
            admins = [{"id": row["telegram_id"]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()
    return admins


async def add_user_to_register_queue(telegram_id: int, username: str) -> None:
    connection = db_connection()
    try:
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
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()


async def get_all_registered_user() -> list[user]:
    users = []
    conncetion = db_connection()
    try:
        with conncetion.cursor() as cursor:
            sql = "SELECT id, username WHERE is_enabled=1"
            cursor.execute(sql, ())
            users = [
                {"id": user["id"], "username": user["username"]}
                for user in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(str(e))
    finally:
        conncetion.close()
    return users


async def delete_user(telegram_id: int) -> None:
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM users WHERE id = %s;"
            cursor.execute(sql, (telegram_id,))
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()


async def get_current_rider(order_id: int) -> user:
    user = None
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """SELECT users.id, users.username FROM users
            INNER JOIN riders ON riders.telegrm_id = users.id
            INNER JOIN orders ON orders.rider_id = riders.telegram_id
            WHERE orders.id = %s"""
            cursor.execute(sql, (order_id,))
            user = cursor.fetchone()
            user = {"id": user["id"], "username": user["username"]}
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()
    return user


async def delete_user_item(telegram_id: int, item_id: int, order_id: int):
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """DELETE FROM  items 
            WHERE order_id = %s AND
            telegram_id = %s AND
            id = %s"""
            cursor.execute(sql, (order_id, telegram_id, item_id))
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()


async def all_enabled_users() -> list[user]:
    users = []
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """SELECT id, username FROM users
            WHERE is_enabled = 1"""
            cursor.execute(sql)
            users = [
                {
                    "id": user["id"],
                    "username": user["username"],
                }
                for user in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()
    return users


async def set_order_completated(order_id: int) -> None:
    connection = db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """UPDATE orders SET completed = 1 
            WHERE id = %s"""
            cursor.execute(sql, (order_id,))
        connection.commit()
    except Exception as e:
        logger.error(str(e))
    finally:
        connection.close()


async def last_confirmed_order() -> order:
    order = None
    conncetion = db_connection()
    try:
        with conncetion.cursor() as cursor:
            sql = """SELECT id FROM orders 
            WHERE completed = 1
            ORDER BY id ASC
            """
            cursor.execute(sql)
            order = {"id": cursor.fetchone()["id"]}
    except Exception as e:
        logger.error(str(e))
    finally:
        conncetion.close()
    return order


async def total_order_for_each_user(order_id: int) -> list[total]:
    total_users = []
    conncetion = db_connection()
    try:
        with conncetion.cursor() as cursor:
            sql = """SELECT users.username, SUM(items.price) AS total FROM items 
            INNER JOIN orders ON orders.id = items.order_id
            INNER JOIN users ON users.id = items.telegram_id
            WHERE orders.id = %s
            GROUP BY users.username
            ORDER BY users.username ASC
            """
            cursor.execute(sql, (order_id,))
            total_users = [
                {
                    "username": total_user["username"],
                    "total": total_user["total"],
                }
                for total_user in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(str(e))
    finally:
        conncetion.close()
    return total_users
