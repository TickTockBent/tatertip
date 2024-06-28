import discord
from discord.ext import commands
import hashlib
import binascii
import blake3
from bech32 import bech32_encode, convertbits
from config import ADMIN_IDS, BOT_USER_ID
from utils.database import get_user_data, update_user_balance, log_action
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
    
    @commands.command(name='generate_address')
    @commands.check(lambda ctx: ctx.author.id in ADMIN_IDS)
    async def generate_address(self, ctx, public_key: str):
        try:
            address = self.spawn_wallet_address(public_key)
            await ctx.send(f"Generated address:\nRaw: {address['raw_address']}\nBech32: {address['bech32_address']}")
        except Exception as e:
            await ctx.send(f"Error generating address: {str(e)}")

    def blake3_hash(self, data):
        return hashlib.blake3(data).digest()

    def compute_address(self, public_key):
        template = b'\x00' * 23 + b'\x01'
        data = template + public_key
        hashed = self.blake3_hash(data)
        address = b'\x00' * 4 + hashed[-20:]
        return address

    def bech32_encode_address(self, address, hrp="sm"):
        converted = convertbits(address, 8, 5)
        return bech32_encode(hrp, converted)

    def spawn_wallet_address(self, public_key_hex):
        public_key = binascii.unhexlify(public_key_hex)
        
        if len(public_key) != 32:
            raise ValueError("Public key must be 32 bytes long")
        
        raw_address = self.compute_address(public_key)
        bech32_address = self.bech32_encode_address(raw_address)
        
        return {
            "raw_address": binascii.hexlify(raw_address).decode(),
            "bech32_address": bech32_address
        }

async def setup(bot):
    print("Attempting to add Admin cog")
    await bot.add_cog(Admin(bot))
    print("Admin cog added successfully")