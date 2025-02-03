import discord
from discord.ext import commands, tasks
import os
import asyncio
from dotenv import load_dotenv
import pymongo
from datetime import datetime, timezone

CLIENT = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
mydb = CLIENT['authoriszations']
athInfo = mydb.authInformation

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

async def monitorExpired():
    while True:
        currTime = datetime.now(timezone.utc)
        expired = list(athInfo.find(
            {'expiryTime': {'$lt': currTime}},
            {'emailAdress':1}
        ))

        for doc in expired:
            athInfo.delete_one({'_id': doc['_id']})
           
        await asyncio.sleep(1) 

async def main():
    athInfo.create_index([("expiryTime", 1)], expireAfterSeconds=0)

    async with bot:
        asyncio.create_task(monitorExpired())
        await load()
        await bot.start(TOKEN) 
    athInfo.drop_indexes()

asyncio.run(main())