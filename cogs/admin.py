import discord
from discord.ext import commands
from config import ADMIN_IDS, BOT_USER_ID
from utils.database import get_user_data, log_action

def is_admin():
    async def predicate(ctx):
        return ctx.author.id in ADMIN_IDS
    return commands.check(predicate)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Admin cog initialized")

    @commands.command(name='addbalance')
    @is_admin()
    async def add_balance(self, ctx, user: discord.User, amount: float):
        if amount <= 0:
            await ctx.send("Amount must be positive.")
            return

        target_user_id = str(user.id)
        
        async with ctx.bot.pool.acquire() as conn:
            user_data = await get_user_data(target_user_id)
            
            if user_data is None:
                await ctx.send(f"User {user.name} (ID: {user.id}) is not registered.")
                return
            
            current_balance = user_data[3]  # Assuming balance is at index 3
            new_balance = current_balance + amount
            
            # Update the user's balance
            await conn.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, target_user_id))
            
            # Log the balance addition
            await log_action('ADD_BALANCE', target_user_id, f'Added: {amount}, New Balance: {new_balance}')
        
        await ctx.send(f"Added {amount} to {user.name}'s balance. New balance: {new_balance}")

    @commands.command(name='removebalance')
    @is_admin()
    async def remove_balance(self, ctx, user: discord.User, amount: float):
        if amount <= 0:
            await ctx.send("Amount must be positive.")
            return

        target_user_id = str(user.id)
        
        async with ctx.bot.pool.acquire() as conn:
            user_data = await get_user_data(target_user_id)
            
            if user_data is None:
                await ctx.send(f"User {user.name} (ID: {user.id}) is not registered.")
                return
            
            current_balance = user_data[3]  # Assuming balance is at index 3
            
            if current_balance < amount:
                await ctx.send(f"User {user.name} (ID: {user.id}) does not have enough balance to remove.")
                return
            
            new_balance = current_balance - amount
            
            # Update the user's balance
            await conn.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, target_user_id))
            
            # Log the balance removal
            await log_action('REMOVE_BALANCE', target_user_id, f'Removed: {amount}, New Balance: {new_balance}')
        
        await ctx.send(f"Removed {amount} from {user.name}'s balance. New balance: {new_balance}")

    @commands.command(name='botbalance')
    @is_admin()
    async def check_bot_balance(self, ctx):
        async with ctx.bot.pool.acquire() as conn:
            cursor = await conn.execute('SELECT balance FROM users WHERE user_id = ?', (BOT_USER_ID,))
            result = await cursor.fetchone()
            
        if result:
            await ctx.send(f"The bot's current balance is {result[0]} SMH.")
        else:
            await ctx.send("Couldn't retrieve the bot's balance.")

    @add_balance.error
    @remove_balance.error
    async def balance_error(self, ctx, error):
        if isinstance(error, commands.UserNotFound):
            await ctx.send("Could not find that user. Make sure you're using a proper mention, user ID, or username.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid arguments. Usage: !addbalance/@removebalance @user amount")
        else:
            await ctx.send(f"An unexpected error occurred: {str(error)}")
            # Log the full error for debugging
            print(f"Error in balance command: {error}")

def setup(bot):
    bot.add_cog(Admin(bot))