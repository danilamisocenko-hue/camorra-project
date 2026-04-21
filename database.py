import aiosqlite
import sqlite3

DB_PATH = "camorra.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT
            )""")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                wallet_address TEXT,
                network TEXT,
                label TEXT
            )""")
        await db.commit()

async def add_user(user_id, username, first_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                       (user_id, username, first_name))
        await db.commit()

async def get_admin_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            u_count = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM wallets") as cursor:
            w_count = (await cursor.fetchone())[0]
        return u_count, w_count

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def add_wallet(user_id, address, network, label):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO wallets (user_id, wallet_address, network, label) VALUES (?, ?, ?, ?)",
                       (user_id, address, network, label))
        await db.commit()

def get_user_wallets_sync(user_id):
    # Эта функция нужна для клавиатур
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM wallets WHERE user_id = ?", (user_id,))
    res = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return res

async def delete_wallet(user_id, address):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM wallets WHERE user_id = ? AND wallet_address = ?", (user_id, address))
        await db.commit()

async def update_label(user_id, address, new_label):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE wallets SET label = ? WHERE user_id = ? AND wallet_address = ?", (new_label, user_id, address))
        await db.commit()
