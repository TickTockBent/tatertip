import discord
from discord.ext import commands
from config import ADMIN_IDS, BOT_USER_ID
from utils.database import get_user_data, log_action
from utils.db_utils import get_db_connection

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
        
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute('SELECT balance FROM users WHERE user_id = ?', (target_user_id,))
                result = await cur.fetchone()
                
                if result is None:
                    await ctx.send(f"User {user.name} (ID: {user.id}) is not registered.")
                    return
                
                current_balance = result[0]
                new_balance = current_balance + amount
                
                await cur.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, target_user_id))
                await conn.commit()
        
        await ctx.send(f"Added {amount} to {user.name}'s balance. New balance: {new_balance}")

async def setup(bot):
    print("Attempting to add Admin cog")
    await bot.add_cog(Admin(bot))
    print("Admin cog added successfully")