import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import json
import pymongo
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]
CLIENT = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
mydb = CLIENT['authoriszations']
athInfo = mydb.authInformation

class Login(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creds = None
        self.flow = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("commands ready")

    def isExpired(self, timeString):
        timeStamp = datetime.fromisoformat(timeString.replace('Z', '+00:00'))
        currentTime = datetime.now(timeStamp.tzinfo)
        return currentTime > timeStamp

    @app_commands.command(name="login", description="get token of google account")
    async def getCreds(self, interaction: discord.Interaction, emailaddress: str):
        tokenExpired = False
        if athInfo.count_documents({
            "$and": [
                {"emailAdress": emailaddress},
                {"dcUserId": interaction.user.id}
            ]
        }) != 0:
            tokenInfo = athInfo.find_one({'emailAdress': emailaddress, 'dcUserId': interaction.user.id}, {'_id':0, 'tokenInfo':1})['tokenInfo']
            
            if not self.isExpired(tokenInfo['expiry']):
                await interaction.response.send_message(f"Hi, {interaction.user.mention}, we already got your token", ephemeral=True)
                return
                #self.creds = Credentials.from_authorized_user_file(tokenInfo, SCOPES)
            tokenExpired = True
            
        # 1. token is expired - need to get a new one
        # 2. gmail hasn't been authorized
        
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            f"Hi, {interaction.user.mention}, starting authentication process...",
            ephemeral=True
        )

        self.flow = InstalledAppFlow.from_client_secrets_file(
            "./credentials.json", SCOPES
        )

        self.creds = self.flow.run_local_server(port=0)
        
        await interaction.followup.send(
            f"Authentication successful! Credentials saved. We got your token!!!!",
            ephemeral=True
        )

        if tokenExpired:
            athInfo.update_one(
                    {"emailAdress": emailaddress, "dcUserId": interaction.user.id},
                    {"$set": {"token": json.loads(self.creds.to_json())}}
            )
        else:
            info = {
                'emailAdress': emailaddress,
                'dcUserId': interaction.user.id,
                'tokenInfo': json.loads(self.creds.to_json()),
                'expiryTime': datetime.fromisoformat(json.loads(self.creds.to_json())['expiry'].replace('Z', '+00:00')),
                'isActive': False
            }
            
            athInfo.insert_one(info)
                
async def setup(bot):
    await bot.add_cog(Login(bot))