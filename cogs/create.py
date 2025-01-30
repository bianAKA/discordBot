import discord
from discord.ext import commands
from discord import app_commands
import pymongo
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]
CLIENT = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
mydb = CLIENT['authoriszations']
idInfo = mydb.documentId
athInfo = mydb.authInformation

class AddDocument(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("ready to create document/files")
        
    @app_commands.command(name="activate", description="tell the bot which account you are using")
    async def active(self, interaction: discord.Interaction, email: str):
        athInfo.create_index([("emailAdress", 1), ("dcUserId", 1)])
        athInfo.create_index([("isActive", 1), ("dcUserId", 1)])

        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            f"Hi, {interaction.user.mention}, we are finding your email address",
            ephemeral=True
        )

        if athInfo.count_documents({
            "$and": [
                {"emailAdress": email},
                {"dcUserId": interaction.user.id}
            ]
        }) != 0:
            emailTarget = athInfo.find_one({
                "isActive": True,
                "dcUserId": interaction.user.id
            }, {
                "_id":0,
                "emailAdress": 1
            })
    
            if emailTarget:
                await interaction.followup.send(
                    f"Hi, {interaction.user.mention}, it seems like one of your account: {email}, is active right now. If it's not the acount you want to use you can use /end to deactivate it."
                )
            else:
                athInfo.update_one(
                    {"emailAdress": email, "dcUserId": interaction.user.id},
                    {"$set": {"isActive": True}}
                )

                await interaction.followup.send(
                    f"Hi, {interaction.user.mention}, you can now edit/add file/folder!",
                    ephemeral=True
                )
        else:
            await interaction.followup.send(
                f"Hi, {interaction.user.mention}, we couldn't find your email address. Please check if the email address is correct, or use /login command",
                ephemeral=True
            )
        
        athInfo.drop_indexes()

    @app_commands.command(name="end", description="tell the bot which account you want to end")
    async def deActive(self, interaction: discord.Interaction, email: str):
        return
    
    @app_commands.command(name="create_file", description="create a file")
    async def fileCreate(self, interaction: discord.Interaction):
        return

    @app_commands.command(name="create_folder", description="create a folder")
    async def folderCreate(self, interaction: discord.Interaction):
        return
    
async def setup(bot):
    await bot.add_cog(AddDocument(bot))
