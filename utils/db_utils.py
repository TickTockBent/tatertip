import aiosqlite
from config import DB_FILE

async def get_db_connection():
    return await aiosqlite.connect(DB_FILE)