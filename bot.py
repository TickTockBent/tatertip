import discord
from discord.ext import commands
import aiosqlite
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

DB_FILE = 'user_data.db'

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        # Create users table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                wallet_address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Create audit log table
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

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await init_db()

@bot.command(name='register')
async def register(ctx, wallet_address: str):
    user_id = str(ctx.author.id)
    
    async with aiosqlite.connect(DB_FILE) as db:
        # Check if user is already registered
        cursor = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        if await cursor.fetchone():
            await ctx.send("You are already registered!")
            return
        
        # TODO: Add wallet address validation here
        
        # Register new user
        await db.execute('INSERT INTO users (user_id, wallet_address) VALUES (?, ?)', (user_id, wallet_address))
        
        # Log the registration action
        await db.execute('INSERT INTO audit_log (action, user_id, details) VALUES (?, ?, ?)', 
                         ('REGISTER', user_id, f'Wallet: {wallet_address}'))
        
        await db.commit()
    
    await ctx.send(f"Registration successful! Your wallet {wallet_address} has been linked to your account.")

bot.run('YOUR_BOT_TOKEN_HERE')