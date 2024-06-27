import discord
from discord.ext import commands
from config import MIN_TIP_AMOUNT, MAX_TIP_AMOUNT, BOT_USER_ID
from utils.database import get_user_data, update_user_balance, log_action

class Tipping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Tipping cog initialized")

    @commands.command(name='tip')
    async def tip(self, ctx, recipient: discord.User, amount: float):
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

        # Check if tipper is registered and has sufficient balance
        tipper_data = await get_user_data(tipper_id)

        if not tipper_data:
            await ctx.send("You need to register first. Use !register <wallet_address>")
            return

        tipper_balance = tipper_data[3]  # Assuming balance is at index 3

        if tipper_balance < amount:
            await ctx.send("Insufficient balance for this tip.")
            return

        # Check if recipient is registered
        recipient_data = await get_user_data(recipient_id)

        if not recipient_data:
            # Create entry for unregistered user
            await update_user_balance(recipient_id, amount, 'UNREGISTERED')
            await ctx.send(f"{recipient.name} is not registered. A balance has been created for them.")
        else:
            # Update recipient's balance
            await update_user_balance(recipient_id, amount)

        # Update tipper's balance
        new_tipper_balance = tipper_balance - amount
        await update_user_balance(tipper_id, -amount)

        # Log the transaction
        await log_action('TIP', tipper_id, f'Tipped {amount} SMH to {recipient_id}')

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
    async def tip_error(self, ctx, error):
        if isinstance(error, commands.UserNotFound):
            await ctx.send("Could not find that user. Make sure you're using a proper mention or user ID.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid arguments. Usage: !tip @user amount")
        else:
            await ctx.send(f"An unexpected error occurred: {str(error)}")
            # Log the full error for debugging
            print(f"Error in tip command: {error}")

def setup(bot):
    bot.add_cog(Tipping(bot))