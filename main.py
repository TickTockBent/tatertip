import discord
import asyncio
import aiosqlite
from discord.ext import commands
from config import BOT_TOKEN, DB_FILE
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

async def load_extensions():
    for extension in initial_extensions:
        try:
            print(f"Attempting to load extension: {extension}")
            await bot.load_extension(extension)
            print(f"Successfully loaded extension: {extension}")
        except Exception as e:
            print(f"Failed to load extension {extension}: {str(e)}")

async def shutdown(signal, loop):
    print(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

def handle_exception(loop, context):
    msg = context.get("exception", context["message"])
    print(f"Caught exception: {msg}")
    asyncio.create_task(shutdown(signal.SIGINT, loop))

async def main():
    loop = asyncio.get_running_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s, loop))
        )
    
    loop.set_exception_handler(handle_exception)
    
    await load_extensions()
    async with bot:
        await bot.start(BOT_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())