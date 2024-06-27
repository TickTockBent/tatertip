import discord
from discord.ext import commands
from config import BOT_TOKEN
from utils.database import init_db

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    print(f'Command prefix is: {bot.command_prefix}')
    await init_db()

async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        print(f"Command not found: {ctx.message.content}")
    else:
        print(f"An error occurred: {str(error)}")

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')

# Load cogs
initial_extensions = ['cogs.registration', 'cogs.tipping', 'cogs.admin', 'cogs.user_info']

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

bot.run(BOT_TOKEN)