import discord
from discord.ext import commands
from utils.database import get_user_data
from utils.address_generator import validate_spacemesh_address

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("User Info cog initialized")

    @commands.command(name='balance')
    async def check_balance(self, ctx):
        user_id = str(ctx.author.id)
        
        user_data = await get_user_data(user_id)
        
        if user_data:
            wallet_address, deposit_address, balance = user_data[1], user_data[2], user_data[3]
            
            balance_message = f"Your balance is {balance} SMH"
            wallet_message = f"Wallet: {wallet_address}"
            
            if wallet_address == 'UNREGISTERED':
                wallet_message += "\nPlease use !register <wallet_address> to set your withdrawal wallet."
            
            deposit_message = f"To add funds, send SMH to this deposit address:\n{deposit_address}"
            
            full_message = f"{balance_message}\n\n{wallet_message}\n\n{deposit_message}"
            
            await ctx.send(full_message, ephemeral=True)
        else:
            await ctx.send("You are not registered. Use !register <wallet_address> to register.", ephemeral=True)

    @commands.command(name='deposit')
    async def show_deposit_address(self, ctx):
        user_id = str(ctx.author.id)
        
        user_data = await get_user_data(user_id)
        
        if user_data:
            deposit_address = user_data[2]
            await ctx.send(f"Your deposit address is: {deposit_address}\nSend SMH to this address to add funds to your account.", ephemeral=True)
        else:
            await ctx.send("You are not registered. Use !register <wallet_address> to register and get a deposit address.", ephemeral=True)

    @commands.command(name='wallet')
    async def show_wallet(self, ctx):
        user_id = str(ctx.author.id)
        
        user_data = await get_user_data(user_id)
        
        if user_data:
            wallet_address = user_data[1]
            if wallet_address == 'UNREGISTERED':
                await ctx.send("You haven't set a withdrawal wallet yet. Use !register <wallet_address> to set one.", ephemeral=True)
            else:
                await ctx.send(f"Your registered withdrawal wallet is: {wallet_address}", ephemeral=True)
        else:
            await ctx.send("You are not registered. Use !register <wallet_address> to register.", ephemeral=True)

    @commands.command(name='help')
    async def help_command(self, ctx):
        help_text = """
        **TaterTipBot Commands:**

        - `!register <wallet_address>` - Register your wallet address with the bot.
        - `!balance` - Check your current balance and deposit address.
        - `!deposit` - Show your deposit address.
        - `!wallet` - Show your registered withdrawal wallet.
        - `!tip @user <amount>` - Tip another user. Amount must be between {min_tip} and {max_tip} SMH.

        For any issues or questions, please contact an admin.
        """.format(min_tip=self.bot.min_tip, max_tip=self.bot.max_tip)

        await ctx.send(help_text, ephemeral=True)

    @help_command.error
    async def help_command_error(self, ctx, error):
        await ctx.send("An error occurred while displaying the help message. Please try again later or contact an admin.")
        print(f"Error in help command: {error}")

def setup(bot):
    bot.add_cog(UserInfo(bot))