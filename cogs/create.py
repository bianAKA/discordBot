import discord
from discord.ext import commands
from discord import app_commands
import pymongo
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from typing import Optional

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
        
    def getEmail(self, interaction: discord.Interaction):        
        token = athInfo.find_one(
            {"dcUserId": interaction.user.id, "isActive": True},
            {"emailAdress": 1}
        )
        
        return token["emailAdress"]

    async def getCred(self, interaction: discord.Interaction):
        token = athInfo.find_one(
            {"dcUserId": interaction.user.id, "isActive": True},
            {"tokenInfo": 1}
        )
       
        if token is None:
            await interaction.response.send_message(
                f"Hi, {interaction.user.mention}, your authorization of the email is either expired or is not valid. Please login and active it again"
            )
            
            return None
        
        return Credentials.from_authorized_user_info(token["tokenInfo"], SCOPES)      
    
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
    
    def createMetaData_File(self, fileName: str, folderId: Optional[int] = None):
        if folderId is None:
            return {
                'name': fileName,
                'mimeType': 'application/vnd.google-apps.document'
            }
        else:
            return {
                'name': fileName,
                'parents': [folderId],
                'mimeType': 'application/vnd.google-apps.document'
            }
    
    @app_commands.command(name="createfile", description="create a file")
    async def fileCreate(self, interaction: discord.Interaction, file_name: str, folder_id: Optional[int] = None):
        await interaction.response.defer(ephemeral=True)
        creds = await self.getCred(interaction)
    
        if creds is None:
            await interaction.followup.send(
                f"Hi, {interaction.user.mention}, please make sure your email address has a valid authorization",
                ephemeral=True
            )
            
            return
            
        drive_service = build('drive', 'v3', credentials=creds)
        doc = drive_service.files().create(body=self.createMetaData_File(file_name, folder_id)).execute()

        info = {
            'isFile': True,
            'dcUserId': interaction.user.id,
            'emailAdress': self.getEmail(interaction),
            'id': doc['id']
        }
        
        idInfo.insert_one(info)

        await interaction.followup.send(
                f"Hi, {interaction.user.mention}, file is created!",
                ephemeral=True
            )

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
