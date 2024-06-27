import discord
from discord.ext import commands
import aiosqlite
import asyncio
from config import BOT_TOKEN, ADMIN_IDS, DB_FILE, MIN_TIP_AMOUNT, MAX_TIP_AMOUNT, BOT_USER_ID, BOT_WALLET

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

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
        cursor = await db.execute('SELECT * FROM users WHERE user_id = ?', (BOT_USER_ID,))
        if not await cursor.fetchone():
            await db.execute('INSERT INTO users (user_id, wallet_address, balance) VALUES (?, ?, ?)', 
                             (BOT_USER_ID, 'BOT_WALLET', 0))
        await db.commit()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await init_db()

@bot.command(name='botbalance')
async def bot_balance(ctx):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('SELECT balance FROM users WHERE user_id = ?', (BOT_USER_ID,))
        result = await cursor.fetchone()
        
    if result:
        await ctx.send(f"The bot's current balance is {result[0]} SMH.")
    else:
        await ctx.send("Couldn't retrieve the bot's balance.")

@bot.command(name='addbalance')
@commands.check(is_admin)
async def add_balance(ctx, user: discord.User, amount: float):
    if amount <= 0:
        await ctx.send("Amount must be positive.")
        return

    target_user_id = str(user.id)
    
    async with aiosqlite.connect(DB_FILE) as db:
        # Check if the target user is registered
        cursor = await db.execute('SELECT balance FROM users WHERE user_id = ?', (target_user_id,))
        result = await cursor.fetchone()
        
        if result is None:
            await ctx.send(f"User {user.name} (ID: {user.id}) is not registered.")
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

@bot.command(name='removebalance')
@commands.check(is_admin)
async def remove_balance(ctx, user: discord.User, amount: float):
    if amount <= 0:
        await ctx.send("Amount must be positive.")
        return

    target_user_id = str(user.id)
    
    async with aiosqlite.connect(DB_FILE) as db:
        # Check if the target user is registered
        cursor = await db.execute('SELECT balance FROM users WHERE user_id = ?', (target_user_id,))
        result = await cursor.fetchone()
        
        if result is None:
            await ctx.send(f"User {user.name} (ID: {user.id}) is not registered.")
            return
        
        current_balance = result[0]
        
        if current_balance < amount:
            await ctx.send(f"User {user.name} (ID: {user.id}) does not have enough balance to remove.")
            return
        
        new_balance = current_balance - amount
        
        # Update the user's balance
        await db.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, target_user_id))
        
        # Log the balance removal
        await db.execute('INSERT INTO audit_log (action, user_id, details) VALUES (?, ?, ?)', 
                            ('REMOVE_BALANCE', target_user_id, f'Removed: {amount}, New Balance: {new_balance}'))
        
        await db.commit()
    
    await ctx.send(f"Removed {amount} from {user.name}'s balance. New balance: {new_balance}")

@add_balance.error
async def add_balance_error(ctx, error):
    if isinstance(error, commands.UserNotFound):
        await ctx.send("Could not find that user. Make sure you're using a proper mention, user ID, or username.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid arguments. Usage: !addbalance @user amount")
    else:
        await ctx.send(f"An unexpected error occurred: {str(error)}")
        # Log the full error for debugging
        print(f"Error in add_balance: {error}")

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
async def register(ctx, wallet_address: str = None):
    user_id = str(ctx.author.id)
    
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute('SELECT wallet_address FROM users WHERE user_id = ?', (user_id,))
        user_data = await cursor.fetchone()
        
        if not wallet_address:
            if user_data:
                await ctx.send("You are already registered. If you want to update your wallet, please provide a new wallet address.", ephemeral=True)
            else:
                await db.execute('INSERT INTO users (user_id, wallet_address, balance) VALUES (?, ?, ?)', (user_id, 'UNREGISTERED', 0))
                await db.commit()
                await ctx.send("You've been registered with an unregistered wallet. Please use !register <wallet_address> to set your wallet.", ephemeral=True)
            return

        if not user_data:
            # New user registering with a wallet address
            await db.execute('INSERT INTO users (user_id, wallet_address, balance) VALUES (?, ?, ?)', (user_id, wallet_address, 0))
            await db.commit()
            await ctx.send(f"Registration successful! Your wallet {wallet_address} has been linked to your account.", ephemeral=True)
        elif user_data[0] == 'UNREGISTERED':
            # Existing user with 'UNREGISTERED' wallet setting their wallet address
            await db.execute('UPDATE users SET wallet_address = ? WHERE user_id = ?', (wallet_address, user_id))
            await db.commit()
            await ctx.send(f"Your wallet has been updated to: {wallet_address}", ephemeral=True)
        else:
            # Existing user with a registered wallet
            old_wallet = user_data[0]
            if old_wallet != wallet_address:
                await ctx.send(f"You're already registered with wallet: {old_wallet}\n"
                               f"To update to the new wallet: {wallet_address}, please confirm.",
                               ephemeral=True)
                # Confirmation logic will be added in the next step
            else:
                await ctx.send(f"You're already registered with this wallet: {old_wallet}", ephemeral=True)

        # Log the registration action
        await db.execute('INSERT INTO audit_log (action, user_id, details) VALUES (?, ?, ?)', 
                         ('REGISTER', user_id, f'Wallet: {wallet_address}'))
        
        await db.commit()

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

@bot.command(name='tip')
async def tip(ctx, recipient: discord.User, amount: float):
    # Check if amount is valid
    if amount < MIN_TIP_AMOUNT or amount > MAX_TIP_AMOUNT:
        await ctx.send(f"Tip amount must be between {MIN_TIP_AMOUNT} and {MAX_TIP_AMOUNT} SMH.")
        return

    # Check if user is tipping themselves
    if ctx.author.id == recipient.id:
        await ctx.send("You can't tip yourself!")
        return

    tipper_id = str(ctx.author.id)
    recipient_id = str(recipient.id)

    async with aiosqlite.connect(DB_FILE) as db:
        # Check if tipper is registered and has sufficient balance
        cursor = await db.execute('SELECT balance FROM users WHERE user_id = ?', (tipper_id,))
        tipper_balance = await cursor.fetchone()

        if not tipper_balance:
            await ctx.send("You need to register first. Use !register <wallet_address>")
            return

        if tipper_balance[0] < amount:
            await ctx.send("Insufficient balance for this tip.")
            return

        # Check if recipient is registered
        cursor = await db.execute('SELECT wallet_address FROM users WHERE user_id = ?', (recipient_id,))
        recipient_data = await cursor.fetchone()

        if not recipient_data:
            # Create entry for unregistered user
            await db.execute('INSERT INTO users (user_id, wallet_address, balance) VALUES (?, ?, ?)', 
                             (recipient_id, 'UNREGISTERED', 0))

        # Update balances
        new_tipper_balance = tipper_balance[0] - amount
        await db.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, recipient_id))
        await db.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_tipper_balance, tipper_id))

        # Log the transaction
        await db.execute('INSERT INTO audit_log (action, user_id, details) VALUES (?, ?, ?)', 
                         ('TIP', tipper_id, f'Tipped {amount} SMH to {recipient_id}'))

        await db.commit()

    # Contextual confirmation
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f"Successfully tipped {amount} SMH to {recipient.name}!")
    else:
        await ctx.send(f"{ctx.author.name} tipped {amount} SMH to {recipient.name}!")

    # DM the recipient (only if it's not the bot)
    if recipient_id != BOT_USER_ID:
        try:
            if not recipient_data:
                await recipient.send(f"You received a tip of {amount} SMH from {ctx.author.name}! "
                                     f"Please register your wallet address using the !register command.")
            else:
                await recipient.send(f"You received a tip of {amount} SMH from {ctx.author.name}!")
        except discord.Forbidden:
            # If the bot can't DM the user, send a message in the channel
            await ctx.send(f"Couldn't send a DM to {recipient.name}. They may have DMs disabled.")
    else:
        await ctx.send(f"Thank you for your tip of {amount} SMH to the bot!")

@tip.error
async def tip_error(ctx, error):
    if isinstance(error, commands.UserNotFound):
        await ctx.send("Could not find that user. Make sure you're using a proper mention or user ID.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid arguments. Usage: !tip @user amount")
    else:
        await ctx.send(f"An unexpected error occurred: {str(error)}")
        # Log the full error for debugging
        print(f"Error in tip command: {error}")

@bot.command(name='help')
async def help_command(ctx):
    help_text = """
**TaterTipBot Commands:**

- `!register <wallet_address>` - Register your wallet address with the bot.
- `!balance` - Check your current balance.
- `!tip @user <amount>` - Tip another user. Amount must be between {min_tip} and {max_tip} SMH.
- `!botbalance` - Check the bot's current balance.
- `!checkregistration` - Verify if you're registered and see your wallet address.

For any issues or questions, please contact an admin.
    """.format(min_tip=MIN_TIP_AMOUNT, max_tip=MAX_TIP_AMOUNT)

    await ctx.send(help_text)

@help_command.error
async def help_command_error(ctx, error):
    await ctx.send("An error occurred while displaying the help message. Please try again later or contact an admin.")
    print(f"Error in help command: {error}")

bot.run(BOT_TOKEN)