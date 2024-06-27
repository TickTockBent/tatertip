import aiosqlite
from config import DB_FILE

async def get_db_connection():
    conn = await aiosqlite.connect(DB_FILE)
    return conn