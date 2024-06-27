import aiosqlite
from config import DB_FILE

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                wallet_address TEXT NOT NULL,
                deposit_address TEXT UNIQUE,
                balance REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                user_id TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def get_user_data(user_id):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return await cursor.fetchone()

async def update_user_wallet(user_id, wallet_address):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('UPDATE users SET wallet_address = ? WHERE user_id = ?', (wallet_address, user_id))
        await db.commit()

async def insert_new_user(user_id, wallet_address, deposit_address):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('INSERT INTO users (user_id, wallet_address, deposit_address, balance) VALUES (?, ?, ?, ?)', 
                         (user_id, wallet_address, deposit_address, 0))
        await db.commit()

async def log_action(action, user_id, details):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('INSERT INTO audit_log (action, user_id, details) VALUES (?, ?, ?)', 
                         (action, user_id, details))
        await db.commit()

async def update_user_balance(user_id, amount, wallet=''):
    async with aiosqlite.connect(DB_FILE) as db:
        if wallet:
            await db.execute('''
                INSERT INTO users (user_id, wallet_address, balance) 
                VALUES (?, ?, ?) 
                ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?
            ''', (user_id, wallet, amount, amount))
        else:
            await db.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        await db.commit()