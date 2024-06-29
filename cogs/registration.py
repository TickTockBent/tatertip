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
        print(f"Register command received from user {ctx.author.id}")
        user_id = str(ctx.author.id)
        
        # Check if a wallet address was provided
        message_parts = ctx.message.content.split()
        wallet_address = message_parts[1] if len(message_parts) > 1 else None

        if wallet_address and not validate_spacemesh_address(wallet_address):
            await ctx.send(f"Invalid Spacemesh {NETWORK_CONFIG['HRP'].upper()} address provided. Please check and try again.")
            return

        print(f"Fetching user data for user_id: {user_id}")
        user_data = await get_user_data(user_id)
        print(f"User data retrieved: {user_data}")
        
        if not user_data:
            # New user registration
            print("About to spawn wallet address")
            deposit_address = spawn_wallet_address()
            print(f"Spawned deposit address: {deposit_address}")
            await insert_new_user(user_id, wallet_address or 'UNREGISTERED', deposit_address)
            
            if wallet_address:
                await ctx.send(f"Registration successful! Your wallet address has been set to {wallet_address}. Your deposit address is: {deposit_address}")
            else:
                await ctx.send(f"Registration successful! Your deposit address is: {deposit_address}\nPlease use !register <wallet_address> to set your withdrawal wallet when you're ready.")
        else:
            # Existing user logic
            if not wallet_address:
                await ctx.send(f"You're already registered. Your current wallet address is: {user_data[1]}\nYour deposit address is: {user_data[2]}")
            elif user_data[1] == 'UNREGISTERED':
                await update_user_wallet(user_id, wallet_address)
                await ctx.send(f"Your wallet has been updated to: {wallet_address}")
            elif user_data[1] != wallet_address:
                # Implement wallet update confirmation here
                await ctx.send("Wallet update functionality is not implemented yet.")
            else:
                await ctx.send(f"You're already registered with this wallet: {wallet_address}")

        print(f"Inserting new user: {user_id}, {wallet_address or 'UNREGISTERED'}, {deposit_address}")
        await insert_new_user(user_id, wallet_address or 'UNREGISTERED', deposit_address)
        print("New user inserted successfully")

async def setup(bot):
    print("Attempting to add Registration cog")
    await bot.add_cog(Registration(bot))
    print("Registration cog added successfully")