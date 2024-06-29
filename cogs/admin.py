import discord
from discord.ext import commands
import hashlib
import binascii
import blake3
from bech32 import bech32_encode, convertbits
from config import ADMIN_IDS, BOT_USER_ID
from utils.database import get_user_data, update_user_balance, log_action
from utils.db_utils import get_db_connection
from utils.spacemesh_wallet import spawn_wallet_address
from utils.address_validator import validate_spacemesh_address
from utils.spacemesh_api import send_transaction
from spacemesh.v1 import types_pb2

def is_admin():
    async def predicate(ctx):
        return ctx.author.id in ADMIN_IDS
    return commands.check(predicate)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Admin cog initialized")

    @commands.command(name='addbalance')
    @commands.check(lambda ctx: ctx.author.id in ADMIN_IDS)
    async def add_balance(self, ctx, user: discord.User, amount: float):
        if amount <= 0:
            await ctx.send("Amount must be a positive number.")
            return
        
        user_id = str(user.id)
        user_data = await get_user_data(user_id)

        if not user_data:
            await ctx.send(f"User {user.name} is not registered in the system.")
            return

        await update_user_balance(user_id, amount)
        await log_action('ADMIN_ADD_BALANCE', str(ctx.author.id), f'Added {amount} SMH to {user_id}')

        await ctx.send(f"Successfully added {amount} SMH to {user.name}'s balance.")

    @add_balance.error
    async def add_balance_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.UserNotFound):
            await ctx.send("User not found. Please provide a valid user mention or ID.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid arguments. Usage: !addbalance <user> <amount>")
        else:
            await ctx.send(f"An error occurred: {str(error)}")
            print(f"Error in add_balance command: {error}")

    @commands.command(name='removebalance')
    @commands.check(lambda ctx: ctx.author.id in ADMIN_IDS)
    async def remove_balance(self, ctx, user: discord.User, amount: float):
        if amount <= 0:
            await ctx.send("Amount must be a positive number.")
            return
        
        user_id = str(user.id)
        user_data = await get_user_data(user_id)

        if not user_data:
            await ctx.send(f"User {user.name} is not registered in the system.")
            return

        await update_user_balance(user_id, -amount)
        await log_action('ADMIN_REMOVE_BALANCE', str(ctx.author.id), f'Removed {amount} SMH from {user_id}')

        await ctx.send(f"Successfully removed {amount} SMH from {user.name}'s balance.")

    @remove_balance.error
    async def remove_balance_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.UserNotFound):
            await ctx.send("User not found. Please provide a valid user mention or ID.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid arguments. Usage: !removebalance <user> <amount>")
        else:
            await ctx.send(f"An error occurred: {str(error)}")
            print(f"Error in remove_balance command: {error}")

    @commands.command(name='setbalance')
    @commands.check(lambda ctx: ctx.author.id in ADMIN_IDS)
    async def set_balance(self, ctx, user: discord.User, amount: float):
        if amount <= 0:
            await ctx.send("Amount must be a positive number.")
            return
        
        user_id = str(user.id)
        user_data = await get_user_data(user_id)

        if not user_data:
            await ctx.send(f"User {user.name} is not registered in the system.")
            return

        await update_user_balance(user_id, amount - user_data[3])
        await log_action('ADMIN_SET_BALANCE', str(ctx.author.id), f'Set {user.name}\'s balance to {amount} SMH')

        await ctx.send(f"Successfully set {user.name}'s balance to {amount} SMH.")

    @set_balance.error
    async def set_balance_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.UserNotFound):
            await ctx.send("User not found. Please provide a valid user mention or ID.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid arguments. Usage: !setbalance <user> <amount>")
        else:
            await ctx.send(f"An error occurred: {str(error)}")
            print(f"Error in set_balance command: {error}")

    @commands.command(name='getbalance')
    @commands.check(lambda ctx: ctx.author.id in ADMIN_IDS)
    async def get_balance(self, ctx, user: discord.User):
        user_id = str(user.id)
        user_data = await get_user_data(user_id)

        if not user_data:
            await ctx.send(f"User {user.name} is not registered in the system.")
            return

        await ctx.send(f"{user.name}'s balance is {user_data[3]} SMH.")

    @get_balance.error
    async def get_balance_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.UserNotFound):
            await ctx.send("User not found. Please provide a valid user mention or ID.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid arguments. Usage: !getbalance <user>")
        else:
            await ctx.send(f"An error occurred: {str(error)}")
            print(f"Error in get_balance command: {error}")

    @commands.command(name='getdepositaddress')
    @commands.check(lambda ctx: ctx.author.id in ADMIN_IDS)
    async def get_deposit_address(self, ctx, user: discord.User):
        """Admin command to get the deposit address for a user"""
        user_id = user.id
        deposit_address = spawn_wallet_address(user_id)
        
        await ctx.send(f"Deposit address for user {user.name} (ID: {user_id}):\n`{deposit_address}`")

    @get_deposit_address.error
    async def get_deposit_address_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.UserNotFound):
            await ctx.send("User not found. Please provide a valid user mention or ID.")
        else:
            await ctx.send(f"An error occurred: {str(error)}")
            print(f"Error in get_deposit_address command: {error}")

    @commands.command(name='sendtx')
    @commands.check(lambda ctx: ctx.author.id in ADMIN_IDS)
    async def send_transaction_command(self, ctx, recipient: str, amount: float):
        if not validate_spacemesh_address(recipient):
            await ctx.send(f"Invalid Spacemesh address: {recipient}")
            return

        amount_smidge = int(amount * 1e9)  # Convert SMH to smidge

        response = send_transaction(recipient, amount_smidge)

        if response and response.txstate.state == types_pb2.TransactionState.TRANSACTION_STATE_MEMPOOL:
            await ctx.send(f"Transaction sent successfully. TX ID: {binascii.hexlify(response.txstate.id.id).decode()}")
        else:
            await ctx.send("Failed to send transaction. Check logs for details.")

    @send_transaction_command.error
    async def send_transaction_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid arguments. Usage: !sendtx <recipient_address> <amount>")
        else:
            await ctx.send(f"An error occurred: {str(error)}")
            print(f"Error in send_transaction command: {error}")

async def setup(bot):
    print("Attempting to add Admin cog")
    await bot.add_cog(Admin(bot))
    print("Admin cog added successfully")