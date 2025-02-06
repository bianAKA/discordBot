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
        
        if token is None:
            return None
        
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
    
    async def getId(self, name: str, interaction: discord.Interaction, isFile: bool):
        idInfos = idInfo.find_one(
            {"dcUserId": interaction.user.id, 'name': name, 'isFile': isFile},
            {'id': 1}
        )
        
        if idInfos is None:
            await interaction.followup.send(
                f"cannot find your file/directory in our database",
                ephemeral=True
            )
            
            return None
        else:
            return idInfos['id']
    
    async def getParentFolderN(self, name: str, interaction: discord.Interaction, isFile: bool):
        drive_service = await self.getDriveService(interaction)
        if drive_service is None:
            return 'n/a'

        instance = drive_service.files().get(
            fileId= await self.getId(name, interaction, isFile),
            fields='parents'
        ).execute()

        if 'parents' in instance:
            parent = drive_service.files().get(fileId=instance['parents'][0]).execute()
            return parent['name']
        else:
            return "Root"

    async def createMetaData_File(self, fileName: str, interaction: discord.Interaction, folderName: Optional[str] = None):
        if folderName is None:
            return {
                'name': fileName,
                'mimeType': 'application/vnd.google-apps.document'
            }
        else:
            return {
                'name': fileName,
                'parents': [await self.getId(folderName, interaction, isFile=False)],
                'mimeType': 'application/vnd.google-apps.document'
            }
            
    async def createMedaData_Folder(self, folderName: str, interaction: discord.Interaction, parentFolderN: Optional[str] = None):
        if parentFolderN is None:
            return {
                'name': folderName,
                'mimeType': 'application/vnd.google-apps.folder',
            }
        else:
            return {
                'name': folderName,
                'parents': [await self.getId(parentFolderN, interaction, isFile=False)],  
                'mimeType': 'application/vnd.google-apps.folder',
            }
    
    async def getDriveService(self, interaction: discord.Interaction):
        creds = await self.getCred(interaction)
    
        if creds is None:
            await interaction.followup.send(
                f"Hi, {interaction.user.mention}, please make sure your email address has a valid authorization",
                ephemeral=True
            )
            
            return None
        
        return build('drive', 'v3', credentials=creds)
    
    async def getDocService(self, interaction: discord.Interaction):
        creds = await self.getCred(interaction)
        
        if creds is None:
            await interaction.followup.send(
                f"Hi, {interaction.user.mention}, please make sure your email address has a valid authorization",
                ephemeral=True
            )
            
            return None

        return build('docs', 'v1', credentials=creds)
    
    @app_commands.command(name="createfile", description="create a file")
    async def fileCreate(self, interaction: discord.Interaction, file_name: str, folder_name: Optional[str] = None):
        await interaction.response.defer(ephemeral=True)
        drive_service = await self.getDriveService(interaction)
        if drive_service is None:
            return

        metaData = await self.createMetaData_File(file_name, interaction, folder_name)
        doc = drive_service.files().create(body=metaData).execute()

        info = {
            'isFile': True,
            'dcUserId': interaction.user.id,
            'emailAdress': self.getEmail(interaction),
            'name': file_name,
            'id': doc['id']
        }
        
        idInfo.insert_one(info)

        await interaction.followup.send(
                f"Hi, {interaction.user.mention}, file is created!",
                ephemeral=True
            )

    @app_commands.command(name="deletefile", description="delete a file")
    async def fileDelete(self, interaction: discord.Interaction, file_name: str):
        await interaction.response.defer(ephemeral=True)
        drive_service = await self.getDriveService(interaction)
        
        if drive_service is None:
            return

        theId = await self.getId(file_name, interaction, isFile=True)
        
        if theId is None:
            return

        drive_service.files().delete(fileId=theId).execute()
       
        idInfo.delete_one({
            'dcUserId': interaction.user.id, 
            'id': theId,
            'name': file_name,
            'isFile': True
        })

        await interaction.followup.send(
            f"Hi, {interaction.user.mention}, file is deleted",
            ephemeral=True
        )

    @app_commands.command(name="display", description="know all your files and folders")
    async def display(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        emailAdress = self.getEmail(interaction)
        
        if emailAdress is None:
            interaction.followup.send(
                f"Might need to use /activate command to activate your emailaddress",
                ephemeral=True
            )
            
            return

        fileL = list(idInfo.find({
            'dcUserId': interaction.user.id, 
            'isFile': True,
            'emailAdress': emailAdress
        }))
        
        folderL = list(idInfo.find({
            'dcUserId': interaction.user.id, 
            'isFile': False,
            'emailAdress': emailAdress
        }))
        
        embed = discord.Embed(title="Display Pages", description="Here are all the folders and files that are created through discord command")
    
        for file in fileL:
            embed.add_field(name=f"File \t", value=f"{file['name']} is in \t {await self.getParentFolderN(file['name'], interaction, True)}", inline=True)   
        for folder in folderL: 
            embed.add_field(name=f"Folder \t", value=f"{folder['name']} is in \t {await self.getParentFolderN(folder['name'], interaction, False)}", inline=True)   
   
        await interaction.followup.send(embed=embed, ephemeral=True)
            
    @app_commands.command(name="createfolder", description="create a folder")
    async def folderCreate(self, interaction: discord.Interaction, folder_name: str, parent_folder_name: Optional[str] = None):
        await interaction.response.defer(ephemeral=True)
        drive_service = await self.getDriveService(interaction)
        
        if drive_service is None:
            return

        metaData = await self.createMedaData_Folder(folder_name, interaction, parent_folder_name)
        folder = drive_service.files().create(body=metaData).execute()
        info = {
            'isFile': False,
            'dcUserId': interaction.user.id,
            'emailAdress': self.getEmail(interaction),
            'name': folder_name,
            'id': folder['id']
        }
        
        idInfo.insert_one(info)

        await interaction.followup.send(
                f"Hi, {interaction.user.mention}, folder is created!",
                ephemeral=True
            )

    @app_commands.command(name="deletefolder", description="delete a folder")
    async def folderDelete(self, interaction: discord.Interaction, folder_name: str):
        await interaction.response.defer(ephemeral=True)
        drive_service = await self.getDriveService(interaction)
        
        if drive_service is None:
            return

        theId = await self.getId(folder_name, interaction, isFile=False)
        
        if theId is None:
            return

        drive_service.files().delete(fileId=theId).execute()
       
        idInfo.delete_one({
            'dcUserId': interaction.user.id, 
            'id': theId,
            'name': folder_name,
            'isFile': False
        })

        await interaction.followup.send(
            f"Hi, {interaction.user.mention}, folder is deleted",
            ephemeral=True
        )
    
    @app_commands.command(name="write", description="write something down")
    async def writing(self, interaction: discord.Interaction, context: str, file_name: str):
        await interaction.response.defer(ephemeral=True)
        doc_service = await self.getDocService(interaction)
        
        if doc_service is None:
            return

        docId = await self.getId(file_name, interaction, True)
        if docId is None:
            return
        
        docEntity = doc_service.documents().get(documentId=docId).execute()
        endIndex = docEntity['body']['content'][-1]['endIndex']
        
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': endIndex - 1
                    },
                    'text': context
                }
            }
        ]
      
        doc_service.documents().batchUpdate(documentId=docId, body={'requests': requests}).execute()
 
        await interaction.followup.send(
                f"Hi, {interaction.user.mention}, it is written now!",
                ephemeral=True
            )
        
async def setup(bot):
    await bot.add_cog(AddDocument(bot))
