import discord
from discord.ext import commands
from discord import app_commands
import os
import os.path
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

class Write(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creds = None
        self.flow = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("commands ready")

    @app_commands.command(name="login", description="get token of google account")
    async def getCreds(self, interaction: discord.Interaction, emailaddress: str):
        if athInfo.count_documents({
            "$and": [
                {"emailAdress": emailaddress},
                {"dcUserId": interaction.user.id},
                {"isAuthorized": True}
            ]
        }) != 0:
            await interaction.response.send_message(f"Hi, {interaction.user.mention}, we already got your token", ephemeral=True)
            
            tokenInfo = athInfo.find({'emailAdress': emailaddress, 'dcUserId': interaction.user.id}, {_id:False, 'token':True})['token']
            self.creds = Credentials.from_authorized_user_file(tokenInfo, SCOPES)
            return
        
        if not self.creds or not self.creds.valid:
            rewritedCreds = False
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
                rewritedCreds = True
            else: 
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
            
            if rewritedCreds:
                athInfo.update_one(
                    {"emailAdress": emailaddress, "dcUserId": interaction.user.id},
                    {"$set": {"token": self.creds.to_json()}}
                )
            else:
                info = {
                    'emailAdress': emailaddress,
                    'dcUserId': interaction.user.id,
                    'token': json.loads(self.creds.to_json()),
                    'isAuthorized': True
                }
                
                athInfo.insert_one(info)
                
async def setup(bot):
    await bot.add_cog(Write(bot))