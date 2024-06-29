import discord
from discord.ext import commands
from utils.db_utils import get_db_connection
from utils.database import get_user_data, update_user_wallet, insert_new_user, log_action
from utils.spacemesh_wallet import spawn_wallet_address
from utils.address_validator import validate_spacemesh_address
from config import NETWORK_CONFIG

class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Registration cog initialized")

    @commands.command(name='register')
    async def register(self, ctx):
        user_id = str(ctx.author.id)
        
        # Check if a wallet address was provided
        message_parts = ctx.message.content.split()
        wallet_address = message_parts[1] if len(message_parts) > 1 else None

        if wallet_address and not validate_spacemesh_address(wallet_address):
            await ctx.send(f"Invalid Spacemesh {NETWORK_CONFIG['HRP'].upper()} address provided. Please check and try again.", ephemeral=True)
            return

        user_data = await get_user_data(user_id)
        
        if not user_data:
            # New user registration
            deposit_address = spawn_wallet_address()
            await insert_new_user(user_id, wallet_address or 'UNREGISTERED', deposit_address)
            
            if wallet_address:
                await ctx.send(f"Registration successful! Your wallet address has been set to {wallet_address}. Your deposit address is: {deposit_address}", ephemeral=True)
            else:
                await ctx.send(f"Registration successful! Your deposit address is: {deposit_address}\nPlease use !register <wallet_address> to set your withdrawal wallet when you're ready.", ephemeral=True)
        else:
            # Existing user logic
            if not wallet_address:
                await ctx.send(f"You're already registered. Your current wallet address is: {user_data[1]}\nYour deposit address is: {user_data[2]}", ephemeral=True)
            elif user_data[1] == 'UNREGISTERED':
                await update_user_wallet(user_id, wallet_address)
                await ctx.send(f"Your wallet has been updated to: {wallet_address}", ephemeral=True)
            elif user_data[1] != wallet_address:
                # Implement wallet update confirmation here
                await ctx.send("Wallet update functionality is not implemented yet.", ephemeral=True)
            else:
                await ctx.send(f"You're already registered with this wallet: {wallet_address}", ephemeral=True)

        await log_action('REGISTER', user_id, f'Wallet: {wallet_address or "UNREGISTERED"}')

async def setup(bot):
    print("Attempting to add Registration cog")
    await bot.add_cog(Registration(bot))
    print("Registration cog added successfully")