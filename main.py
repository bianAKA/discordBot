import discord
from discord.ext import commands, tasks
import os
import asyncio
from dotenv import load_dotenv

load_dotenv(".env")
TOKEN: str = os.getenv("TOKEN")

bot = commands.Bot(command_prefix="<3", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot ready!")
    
    try:
        synced_commands = await bot.tree.sync()
        print(f"Synced {len(synced_commands)} commands.")
    except Exception as e:
        print("An error with syncing application commands has occured: ", e)

async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with bot:
        await load()
        await bot.start(TOKEN) 

asyncio.run(main())