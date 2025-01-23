import discord
from discord.ext import commands
from discord import app_commands
import os
import os.path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]

class Write(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.creds = None
        self.flow = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("commands ready")
    
    def writingToken(self):
        print("A")
        with open("token.json", "w") as token:
            token_data = {
                'token': self.creds.token,
                'refresh_token': self.creds.refresh_token,
                'token_uri': self.creds.token_uri,
                'client_id': self.creds.client_id,
                'client_secret': self.creds.client_secret,
                'scopes': self.creds.scopes
            }
            json.dump(token_data, token)
        print("B")
        
    
    @app_commands.command(name="testing", description="see if bot is working")
    async def hi(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Hi, {interaction.user.mention}")

    @app_commands.command(name="password", description="authorize the program to access the google drive")
    async def password(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(f"Thanks, we got it!")
        
        self.creds = self.flow.fetch_token(code=self.message)
        self.writingToken()

    @app_commands.command(name="login", description="get token of google account")
    async def getCreds(self, interaction):
        if os.path.exists("token.json"):
            await interaction.response.send_message(f"Hi, {interaction.user.mention}, we already got your token", ephemeral=True)
            
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES) 
            return

        if not self.creds or not self.creds.valid: 
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
                self.writingToken()
            else:
                self.flow = InstalledAppFlow.from_client_secrets_file(
                    "./credentials.json", SCOPES,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob' 
                )

                auth_url = self.flow.authorization_url()
            
                await interaction.response.send_message(f"Hi, {interaction.user.mention}, please go to this link: {auth_url[0]}, and give us the password by using slash command password", ephemeral=True)
                
async def setup(bot):
    await bot.add_cog(Write(bot))