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
        
    def isExist(self, email, id):
        return athInfo.count_documents({
            "$and": [
                {"emailAdress": email},
                {"dcUserId": id}
            ]
        }) != 0
        
    async def updateActive(self, plsActive, interaction: discord.Interaction, email):
        athInfo.update_one(
            {"emailAdress": email, "dcUserId": interaction.user.id},
            {"$set": {"isActive": plsActive}}
        )

        text = ""
        if plsActive:
            text = f"Hi, {interaction.user.mention}, you can now edit/add file/folder!"
        else:
            text = f"Hi, {interaction.user.mention},it stops now"
        
        await interaction.followup.send(text, ephemeral=True)
        
    @app_commands.command(name="activate", description="tell the bot which account you are using")
    async def active(self, interaction: discord.Interaction, email: str):
        athInfo.create_index([("emailAdress", 1), ("dcUserId", 1)])
        athInfo.create_index([("isActive", 1), ("dcUserId", 1)])

        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            f"Hi, {interaction.user.mention}, we are finding your email address",
            ephemeral=True
        )

        if self.isExist(email, interaction.user.id):
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
                await self.updateActive(True, interaction, email)
        else:
            await interaction.followup.send(
                f"Hi, {interaction.user.mention}, we couldn't find your email address. Please check if the email address is correct, or use /login command",
                ephemeral=True
            )
        
        athInfo.drop_indexes()

    @app_commands.command(name="end", description="tell the bot which account you want to end")
    async def deActive(self, interaction: discord.Interaction, email: str):
        athInfo.create_index([("emailAdress", 1), ("dcUserId", 1), ("isActive", 1)])

        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            f"Hi, {interaction.user.mention}, we are finding your email address",
            ephemeral=True
        )

        if self.isExist(email, interaction.user.id):
            emailTarget = athInfo.find_one({
                "isActive": True,
                "dcUserId": interaction.user.id,
                "emailAdress": email
            }, {
                "_id":0,
                "emailAdress": 1
            })
    
            if emailTarget:
                await self.updateActive(False, interaction, email)
            else:
                await interaction.followup.send(
                    f"Hi, {interaction.user.mention}, it seems like one of your account: {email}, is deactive right now."
                )
        else:
            await interaction.followup.send(
                f"Hi, {interaction.user.mention}, we couldn't find your email address. Please check if the email address is correct, or use /login command",
                ephemeral=True
            )
        
        athInfo.drop_indexes()
    
    @app_commands.command(name="create_file", description="create a file")
    async def fileCreate(self, interaction: discord.Interaction):
        return

    @app_commands.command(name="create_folder", description="create a folder")
    async def folderCreate(self, interaction: discord.Interaction):
        return
    
    @app_commands.command(name="delete_file", description="delete a file")
    async def fileDelete(self, interaction: discord.Interaction):
        return

    @app_commands.command(name="delete_folder", description="delete a folder")
    async def folderDelete(self, interaction: discord.Interaction):
        return
    
async def setup(bot):
    await bot.add_cog(AddDocument(bot))
