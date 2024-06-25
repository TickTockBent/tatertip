import discord
from discord.ext import commands
import aiosqlite
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

DB_FILE = 'user_data.db'
ADMIN_IDS = [170855291636809728]

def is_admin(ctx):
    return ctx.author.id in ADMIN_IDS

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        # Create users table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                wallet_address TEXT NOT NULL,
                balance REAL DEFAULT 0,
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

@bot.command(name='addbalance')
@commands.check(is_admin)
async def add_balance(ctx, user: discord.Member, amount: float):
    if amount <= 0:
        await ctx.send("Amount must be positive.")
        return

    target_user_id = str(user.id)
    
    async with aiosqlite.connect(DB_FILE) as db:
        # Check if the target user is registered
        cursor = await db.execute('SELECT balance FROM users WHERE user_id = ?', (target_user_id,))
        result = await cursor.fetchone()
        
        if result is None:
            await ctx.send(f"User {user.name} is not registered.")
            return
        
        current_balance = result[0]
        new_balance = current_balance + amount
        
        # Update the user's balance
        await db.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, target_user_id))
        
        # Log the balance addition
        await db.execute('INSERT INTO audit_log (action, user_id, details) VALUES (?, ?, ?)', 
                         ('ADD_BALANCE', target_user_id, f'Added: {amount}, New Balance: {new_balance}'))
        
        await db.commit()
    
    await ctx.send(f"Added {amount} to {user.name}'s balance. New balance: {new_balance}")

@add_balance.error
async def add_balance_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("Could not find that user. Make sure you're using a proper mention or user ID.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid arguments. Usage: !addbalance @user amount")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

@bot.command(name='balance')
async def check_balance(ctx):
    user_id = str(ctx.author.id)
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('SELECT wallet_address, balance FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        
    if result:
        wallet_address, balance = result
        await ctx.send(f"Your balance is {balance} (Wallet: {wallet_address})")
    else:
        await ctx.send("You are not registered. Use !register <wallet_address> to register.")

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
        
        # Register new user with initial balance of 0
        await db.execute('INSERT INTO users (user_id, wallet_address, balance) VALUES (?, ?, ?)', (user_id, wallet_address, 0))
        
        # Log the registration action
        await db.execute('INSERT INTO audit_log (action, user_id, details) VALUES (?, ?, ?)', 
                         ('REGISTER', user_id, f'Wallet: {wallet_address}'))
        
        await db.commit()
    
    await ctx.send(f"Registration successful! Your wallet {wallet_address} has been linked to your account. Initial balance: 0 SMH")

@bot.command(name='checkregistration')
async def check_registration(ctx):
    user_id = str(ctx.author.id)
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('SELECT wallet_address FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        
    if result:
        await ctx.send(f"You are registered with wallet address: {result[0]}")
    else:
        await ctx.send("You are not registered.")

bot.run('MTI1NTI3MjAyMDQ3NjgyMTUzNQ.GkVw5g.7xI6KrQtdkfhP2xAdCVcU75CdrGc_4ML-WACXU')